# Copyright (C) 2026 Pierre Laminette (geoglorus)
#
# Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou le
# modifier selon les termes de la Licence Publique Générale GNU telle que
# publiée par la Free Software Foundation, soit la version 3 de la licence,
# soit (à votre option) toute version ultérieure.
#
# Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS AUCUNE
# GARANTIE ; sans même la garantie implicite de COMMERCIALISATION ou
# D'ADÉQUATION À UN USAGE PARTICULIER. Consultez la Licence Publique Générale
# GNU pour plus de détails.
#
# Assistance au développement et à la mise au point réalisée avec l'aide
# d'une intelligence artificielle (Gemini).

import re
import unicodedata
from collections import defaultdict

from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.lib import EventType, Person
from gramps.gen.plug.docgen import (
    FONT_SERIF,
    PARA_ALIGN_CENTER,
    FontStyle,
    ParagraphStyle,
)
from gramps.gen.plug.menu import (
    BooleanOption,
    EnumeratedListOption,
    FilterOption,
    StringOption,
)
from gramps.gen.plug.report import MenuReportOptions, Report, utils
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback

_ = glocale.translation.gettext


def normalize_sort_key(text):
    """Normalise une chaîne pour le tri alphabétique (sans accents, minuscule)."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


class LivreFamillesOptions(MenuReportOptions):
    def __init__(self, name, dbase):
        super().__init__(name, dbase)

    def add_menu_options(self, menu):
        category = _("Options du répertoire")

        self.title = StringOption(_("Titre du document"), _("Livre des Familles"))
        menu.add_option(category, "title", self.title)

        self.subtitle = StringOption(_("Sous-titre"), "")
        menu.add_option(category, "subtitle", self.subtitle)

        self.filter = FilterOption(_("Filtre de personnes"), 0)
        self.filter.set_help(_("Sélectionner les personnes à inclure (Toutes par défaut)."))
        menu.add_option(category, "filter", self.filter)

        self.notes_mode = EnumeratedListOption(_("Notes"), "all")
        self.notes_mode.add_item("all", _("Toutes les notes"))
        self.notes_mode.add_item("public", _("Uniquement les notes non privées"))
        self.notes_mode.add_item("private", _("Uniquement les notes privées"))
        self.notes_mode.add_item("none", _("Aucune note"))
        menu.add_option(category, "notes_mode", self.notes_mode)

        self.include_legend = BooleanOption(_("Inclure la légende des abréviations"), True)
        menu.add_option(category, "include_legend", self.include_legend)

        sections_cat = _("Sections à générer")

        self.gen_repertoire = BooleanOption(_("Répertoire des familles"), True)
        menu.add_option(sections_cat, "gen_repertoire", self.gen_repertoire)

        self.gen_idx_surnames = BooleanOption(_("Index des patronymes"), True)
        menu.add_option(sections_cat, "gen_idx_surnames", self.gen_idx_surnames)

        self.gen_idx_givens = BooleanOption(_("Index des prénoms"), True)
        menu.add_option(sections_cat, "gen_idx_givens", self.gen_idx_givens)

        self.gen_idx_places = BooleanOption(_("Index des localités"), True)
        menu.add_option(sections_cat, "gen_idx_places", self.gen_idx_places)

        self.gen_idx_occus = BooleanOption(_("Index des professions et fonctions"), True)
        menu.add_option(sections_cat, "gen_idx_occus", self.gen_idx_occus)

        self.gen_idx_spouses = BooleanOption(_("Index des épouses"), True)
        menu.add_option(sections_cat, "gen_idx_spouses", self.gen_idx_spouses)

    def make_default_style(self, default_style):
        """Définit les styles de paragraphe en Liberation Serif."""
        font_title = FontStyle()
        font_title.set(face=FONT_SERIF, size=16, bold=True)
        para_title = ParagraphStyle()
        para_title.set_font(font_title)
        para_title.set_alignment(PARA_ALIGN_CENTER)
        para_title.set_bottom_border(True)
        para_title.set_bottom_margin(utils.pt2cm(8))
        default_style.add_paragraph_style("LF-Title", para_title)

        font_sub = FontStyle()
        font_sub.set(face=FONT_SERIF, size=10, italic=True)
        para_sub = ParagraphStyle()
        para_sub.set_font(font_sub)
        para_sub.set_alignment(PARA_ALIGN_CENTER)
        para_sub.set_bottom_margin(utils.pt2cm(10))
        default_style.add_paragraph_style("LF-Subtitle", para_sub)

        font_entry = FontStyle()
        font_entry.set(face=FONT_SERIF, size=10.5)
        para_entry = ParagraphStyle()
        para_entry.set_font(font_entry)
        para_entry.set_top_margin(utils.pt2cm(8))
        para_entry.set_bottom_margin(utils.pt2cm(1))
        para_entry.set_left_margin(0.8)
        para_entry.set_first_indent(-0.8)
        default_style.add_paragraph_style("LF-EntryHeader", para_entry)

        font_body = FontStyle()
        font_body.set(face=FONT_SERIF, size=10)
        para_body = ParagraphStyle()
        para_body.set_font(font_body)
        para_body.set_left_margin(0.8)
        para_body.set_bottom_margin(utils.pt2cm(1))
        default_style.add_paragraph_style("LF-Body", para_body)

        font_child = FontStyle()
        font_child.set(face=FONT_SERIF, size=10)
        para_child = ParagraphStyle()
        para_child.set_font(font_child)
        para_child.set_left_margin(1.4)
        para_child.set_bottom_margin(utils.pt2cm(1))
        default_style.add_paragraph_style("LF-Child", para_child)

        font_child_sub = FontStyle()
        font_child_sub.set(face=FONT_SERIF, size=9.5)
        para_child_sub = ParagraphStyle()
        para_child_sub.set_font(font_child_sub)
        para_child_sub.set_left_margin(2.0)
        para_child_sub.set_bottom_margin(utils.pt2cm(1))
        default_style.add_paragraph_style("LF-ChildSub", para_child_sub)

        font_idx_h = FontStyle()
        font_idx_h.set(face=FONT_SERIF, size=12, bold=True)
        para_idx_h = ParagraphStyle()
        para_idx_h.set_font(font_idx_h)
        para_idx_h.set_top_margin(utils.pt2cm(10))
        para_idx_h.set_bottom_margin(utils.pt2cm(4))
        default_style.add_paragraph_style("LF-IndexHeader", para_idx_h)


class LivreFamillesReport(Report):
    def __init__(self, database, options, user):
        super().__init__(database, options, user)
        self.db = database
        self.doc = options.handler.doc
        self.user = user
        menu = options.menu

        def _get_val(opt_name, default):
            opt = menu.get_option_by_name(opt_name)
            return opt.get_value() if opt else default

        self.title_text = _get_val("title", _("Livre des Familles"))
        self.subtitle_text = _get_val("subtitle", "")

        filter_opt = menu.get_option_by_name("filter")
        self.filter_obj = None
        if filter_opt and hasattr(filter_opt, "get_filter"):
            try:
                self.filter_obj = filter_opt.get_filter()
            except Exception:
                self.filter_obj = None

        self.notes_mode = _get_val("notes_mode", "all")
        self.include_legend = _get_val("include_legend", True)

        self.gen_repertoire = _get_val("gen_repertoire", True)
        self.gen_idx_surnames = _get_val("gen_idx_surnames", True)
        self.gen_idx_givens = _get_val("gen_idx_givens", True)
        self.gen_idx_places = _get_val("gen_idx_places", True)
        self.gen_idx_occus = _get_val("gen_idx_occus", True)
        self.gen_idx_spouses = _get_val("gen_idx_spouses", True)

        self.entries = []
        self.person_main_entry = {}
        self.person_child_ref = {}
        self.woman_entries = defaultdict(list)

        self.idx_surnames = defaultdict(set)
        self.idx_givens = defaultdict(set)
        self.idx_places = defaultdict(set)
        self.idx_occus = defaultdict(set)
        self.idx_spouses = defaultdict(set)

    def show_completion_dialog(self):
        """Affiche une fenêtre de confirmation avec un bouton Fermer."""
        try:
            import gi

            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk

            parent = None
            if self.user and getattr(self.user, "uistate", None):
                parent = getattr(self.user.uistate, "window", None)

            dialog = Gtk.MessageDialog(
                transient_for=parent,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.NONE,
                text=_("Génération du Livre des Familles terminée avec succès"),
            )
            dialog.add_button(_("Fermer"), Gtk.ResponseType.CLOSE)
            dialog.run()
            dialog.destroy()
        except Exception:
            pass

    def write_line(self, style_name, text):
        if text is None:
            return
        self.doc.start_paragraph(style_name)
        self.doc.write_text(text)
        self.doc.end_paragraph()

    def write_segments(self, style_name, segments):
        if not segments:
            return
        self.doc.start_paragraph(style_name)
        for text, is_bold in segments:
            if text:
                if is_bold:
                    self.doc.start_bold()
                    self.doc.write_text(text)
                    self.doc.end_bold()
                else:
                    self.doc.write_text(text)
        self.doc.end_paragraph()

    def write_blank_line(self, style_name="LF-Body"):
        self.doc.start_paragraph(style_name)
        self.doc.write_text("")
        self.doc.end_paragraph()

    def get_surnames_list(self, person):
        if not person:
            return []
        surnames = []
        primary_name = person.get_primary_name()
        if primary_name:
            for s_obj in primary_name.get_surname_list():
                raw = s_obj.get_surname() or ""
                for part in raw.split(","):
                    cleaned = part.strip()
                    if cleaned and cleaned not in surnames:
                        surnames.append(cleaned)
        return surnames

    def get_given_names(self, person):
        if not person:
            return ""
        return (person.get_primary_name().get_first_name() or "").strip()

    def format_person_plain(self, person):
        if not person:
            return "NN"
        surnames = self.get_surnames_list(person)
        givens = self.get_given_names(person)
        s_str = ", ".join(s.upper() for s in surnames)
        if s_str and givens:
            return f"{s_str} {givens}"
        return s_str or givens or "NN"

    def add_name_segments(self, segs, person, abbrev_surname=False):
        if not person:
            segs.append(("NN", True))
            return
        surnames = self.get_surnames_list(person)
        givens = self.get_given_names(person)
        added_any = False

        if abbrev_surname and surnames:
            segs.append((f"{surnames[0][0].upper()}.", True))
            added_any = True
        elif surnames:
            for idx, s in enumerate(surnames):
                if idx > 0:
                    segs.append((", ", False))
                segs.append((s.upper(), True))
                added_any = True

        if givens:
            if added_any:
                segs.append((" ", False))
            segs.append((givens, False))
            added_any = True

        if not added_any:
            segs.append(("NN", True))

    def format_date(self, event, year_only=False):
        if not event:
            return ""
        date_obj = event.get_date_object()
        if not date_obj or date_obj.is_empty():
            return ""
        year = date_obj.get_year()
        month = date_obj.get_month()
        day = date_obj.get_day()

        prefix = "ax " if date_obj.get_modifier() in (1, 2, 3) else ""
        if year_only and year:
            return f"{prefix}{year:04d}"
        if year and month and day:
            return f"{prefix}{day:02d}.{month:02d}.{year:04d}"
        if year and month:
            return f"{prefix}{month:02d}.{year:04d}"
        if year:
            return f"{prefix}{year:04d}"
        return ""

    def format_event_str(self, symbol, event, entry_num):
        if not event:
            return ""
        d_str = self.format_date(event)
        p_str = self.get_place_name(event, entry_num)
        content = " ".join(x for x in [symbol, d_str, p_str] if x).strip()
        if not content or content == symbol:
            return ""
        return content

    def get_place_name(self, event, entry_num=None):
        if not event:
            return ""
        place_handle = event.get_place_handle()
        if not place_handle:
            return ""
        place = self.db.get_place_from_handle(place_handle)
        if not place:
            return ""
        name = place.get_name().get_value() if place.get_name() else ""
        if not name:
            name = place.get_title() or ""
        name = name.strip()
        if name and entry_num is not None:
            self.idx_places[name].add(entry_num)
        return name

    def get_occupations(self, person, entry_num=None):
        if not person:
            return []
        occus = []
        for event_ref in person.get_event_ref_list():
            event = self.db.get_event_from_handle(event_ref.ref)
            if event and event.get_type() == EventType.OCCUPATION:
                desc = (event.get_description() or "").strip()
                if desc and desc not in occus:
                    occus.append(desc)
                    if entry_num is not None:
                        self.idx_occus[desc].add(entry_num)
        return occus

    def get_notes_texts(self, obj):
        if self.notes_mode == "none" or not obj:
            return []
        texts = []
        for note_handle in obj.get_note_list():
            note = self.db.get_note_from_handle(note_handle)
            if not note:
                continue
            is_private = bool(note.get_privacy())
            if self.notes_mode == "public" and is_private:
                continue
            if self.notes_mode == "private" and not is_private:
                continue
            txt = note.get().strip()
            if txt:
                texts.append(txt)
        return texts

    def get_marriage_event(self, family):
        if not family:
            return None
        for event_ref in family.get_event_ref_list():
            event = self.db.get_event_from_handle(event_ref.ref)
            if event and event.get_type() == EventType.MARRIAGE:
                return event
        return None

    def get_birth_sort_tuple(self, person):
        if not person:
            return (9999, 99, 99)
        b_ev = get_birth_or_fallback(self.db, person)
        if not b_ev:
            return (9999, 99, 99)
        d = b_ev.get_date_object()
        if not d or d.is_empty():
            return (9999, 99, 99)
        return (d.get_year() or 9999, d.get_month() or 99, d.get_day() or 99)

    def get_marriage_sort_tuple(self, family):
        m_ev = self.get_marriage_event(family)
        if not m_ev:
            return (9999, 99, 99)
        d = m_ev.get_date_object()
        if not d or d.is_empty():
            return (9999, 99, 99)
        return (d.get_year() or 9999, d.get_month() or 99, d.get_day() or 99)

    def index_person_names(self, person, entry_num):
        if not person or entry_num is None:
            return
        for s in self.get_surnames_list(person):
            self.idx_surnames[s.upper()].add(entry_num)
        givens = self.get_given_names(person)
        for token in re.split(r"[\s\-]+", givens):
            token = token.strip()
            if token:
                self.idx_givens[token].add(entry_num)

    def index_spouse(self, spouse, entry_num):
        if not spouse or entry_num is None:
            return
        label = self.format_person_plain(spouse)
        if label:
            self.idx_spouses[label].add(entry_num)

    def build_entries(self):
        all_handles = list(self.db.get_person_handles())
        selected_handles = all_handles

        if self.filter_obj and hasattr(self.filter_obj, "apply"):
            try:
                filtered = self.filter_obj.apply(self.db, all_handles)
                if filtered:
                    selected_handles = list(filtered)
            except Exception:
                selected_handles = all_handles

        raw_entries = []

        for p_handle in selected_handles:
            person = self.db.get_person_from_handle(p_handle)
            if not person:
                continue
            fams_handles = person.get_family_handle_list()
            if not fams_handles:
                continue

            gender = person.get_gender()
            if gender == Person.MALE:
                fams = [
                    self.db.get_family_from_handle(fh)
                    for fh in fams_handles
                    if self.db.get_family_from_handle(fh)
                ]
                fams.sort(key=self.get_marriage_sort_tuple)
                raw_entries.append(
                    {
                        "main_person": person,
                        "families": fams,
                        "is_solo_mother": False,
                    }
                )
            elif gender == Person.FEMALE:
                solo_fams = []
                for fh in fams_handles:
                    fam = self.db.get_family_from_handle(fh)
                    if fam and not fam.get_father_handle():
                        solo_fams.append(fam)
                if solo_fams:
                    solo_fams.sort(key=self.get_marriage_sort_tuple)
                    raw_entries.append(
                        {
                            "main_person": person,
                            "families": solo_fams,
                            "is_solo_mother": True,
                        }
                    )

        def entry_sort_key(item):
            p = item["main_person"]
            surnames = self.get_surnames_list(p)
            main_surname = normalize_sort_key(surnames[0]) if surnames else "zzzz"
            given = normalize_sort_key(self.get_given_names(p))
            birth = self.get_birth_sort_tuple(p)
            return (main_surname, given, birth)

        raw_entries.sort(key=entry_sort_key)

        for idx, item in enumerate(raw_entries, start=1):
            item["num"] = idx
            p = item["main_person"]
            self.person_main_entry[p.get_handle()] = idx

            if p.get_gender() == Person.FEMALE:
                self.woman_entries[p.get_handle()].append(idx)

            child_counter = 0
            for fam in item["families"]:
                m_handle = fam.get_mother_handle()
                if m_handle and not item["is_solo_mother"]:
                    if idx not in self.woman_entries[m_handle]:
                        self.woman_entries[m_handle].append(idx)

                for child_ref in fam.get_child_ref_list():
                    child_counter += 1
                    c_handle = child_ref.ref
                    if c_handle not in self.person_child_ref:
                        self.person_child_ref[c_handle] = (idx, child_counter)

        self.entries = raw_entries

    def add_parentage_and_refs_segments(self, segs, person, current_entry_num):
        if not person:
            return
        p_handle = person.get_handle()
        chunks = []

        if person.get_gender() == Person.FEMALE:
            others = [n for n in self.woman_entries.get(p_handle, []) if n != current_entry_num]
            if others:
                chunks.append(("ref_list", ", ".join(str(n) for n in sorted(others))))

        if p_handle in self.person_child_ref:
            f_num, c_num = self.person_child_ref[p_handle]
            chunks.append(("ref_list", f"{f_num}.{c_num}"))

        parent_fam_handle = person.get_main_parents_family_handle()
        pfam = self.db.get_family_from_handle(parent_fam_handle) if parent_fam_handle else None
        father = (
            self.db.get_person_from_handle(pfam.get_father_handle())
            if pfam and pfam.get_father_handle()
            else None
        )
        mother = (
            self.db.get_person_from_handle(pfam.get_mother_handle())
            if pfam and pfam.get_mother_handle()
            else None
        )

        if father or mother:
            chunks.append(("parents", (father, mother)))

        for idx, (kind, payload) in enumerate(chunks):
            segs.append((" " if idx == 0 else ", ", False))
            if kind == "ref_list":
                segs.append(("<", True))
                segs.append((payload, True))
                segs.append((">", True))
            elif kind == "parents":
                f_obj, m_obj = payload
                rel = "fs de " if person.get_gender() == Person.MALE else "fe de "
                segs.append((rel, False))

                p_surnames = set(self.get_surnames_list(person))
                f_surnames = set(self.get_surnames_list(f_obj)) if f_obj else set()
                abbrev_f = bool(p_surnames & f_surnames)

                if f_obj:
                    self.add_name_segments(segs, f_obj, abbrev_surname=abbrev_f)
                if f_obj and m_obj:
                    segs.append((" et ", False))
                if m_obj:
                    self.add_name_segments(segs, m_obj, abbrev_surname=False)

    def write_birth_death_line(self, style_name, person, entry_num):
        b_str = self.format_event_str("*", get_birth_or_fallback(self.db, person), entry_num)
        d_str = self.format_event_str("†", get_death_or_fallback(self.db, person), entry_num)
        if not b_str and not d_str:
            return
        if b_str and d_str:
            self.write_line(style_name, f"{b_str}\t{d_str}")
        else:
            self.write_line(style_name, b_str or d_str)

    def write_entry(self, entry, emit_output=True):
        num = entry["num"]
        main_p = entry["main_person"]

        self.index_person_names(main_p, num)
        occus = self.get_occupations(main_p, num)

        if emit_output:
            header = [(str(num), True), ("\t", False)]
            self.add_name_segments(header, main_p, abbrev_surname=False)
            self.add_parentage_and_refs_segments(header, main_p, num)
            if occus:
                header.append((f", {', '.join(occus)}", False))
            self.write_segments("LF-EntryHeader", header)

            self.write_birth_death_line("LF-Body", main_p, num)

            for note_txt in self.get_notes_texts(main_p):
                self.write_line("LF-Body", note_txt)

        child_global_idx = 0
        for fam_idx, fam in enumerate(entry["families"]):
            if emit_output and fam_idx > 0:
                self.write_blank_line("LF-Body")

            m_ev = self.get_marriage_event(fam)
            if emit_output and m_ev:
                m_str = self.format_event_str("x", m_ev, num)
                if m_str:
                    self.write_line("LF-Body", m_str)

            if not entry["is_solo_mother"]:
                spouse_handle = fam.get_mother_handle()
                spouse = (
                    self.db.get_person_from_handle(spouse_handle) if spouse_handle else None
                )
                if spouse:
                    self.index_person_names(spouse, num)
                    self.index_spouse(spouse, num)
                    sp_occus = self.get_occupations(spouse, num)

                    if emit_output:
                        sp_segs = []
                        self.add_name_segments(sp_segs, spouse, abbrev_surname=False)
                        self.add_parentage_and_refs_segments(sp_segs, spouse, num)
                        if sp_occus:
                            sp_segs.append((f", {', '.join(sp_occus)}", False))
                        self.write_segments("LF-Body", sp_segs)

                        self.write_birth_death_line("LF-Body", spouse, num)

                        for note_txt in self.get_notes_texts(spouse):
                            self.write_line("LF-Body", note_txt)
            elif emit_output:
                self.write_line("LF-Body", _("enfant(s) de père inconnu"))

            if emit_output:
                for note_txt in self.get_notes_texts(fam):
                    self.write_line("LF-Body", note_txt)

            children = [
                self.db.get_person_from_handle(cr.ref)
                for cr in fam.get_child_ref_list()
                if self.db.get_person_from_handle(cr.ref)
            ]

            if emit_output and children:
                self.write_blank_line("LF-Body")

            for child in children:
                child_global_idx += 1
                self.index_person_names(child, num)
                self.get_occupations(child, num)

                b_ev = get_birth_or_fallback(self.db, child)
                d_ev = get_death_or_fallback(self.db, child)
                b_str = self.format_event_str("*", b_ev, num)
                d_str = self.format_event_str("†", d_ev, num)

                if not emit_output:
                    continue

                c_segs = [(f"{child_global_idx}. ", False)]
                self.add_name_segments(c_segs, child, abbrev_surname=False)

                if b_str and d_str:
                    c_segs.append((f" {b_str}\t{d_str}", False))
                    d_str = ""
                elif b_str:
                    c_segs.append((f" {b_str}", False))
                elif d_str:
                    c_segs.append((f"\t{d_str}", False))
                    d_str = ""

                c_handle = child.get_handle()
                if c_handle in self.person_main_entry:
                    c_segs.append((" <", True))
                    c_segs.append((str(self.person_main_entry[c_handle]), True))
                    c_segs.append((">", True))
                elif child.get_gender() == Person.FEMALE and c_handle in self.woman_entries:
                    w_refs = [n for n in self.woman_entries[c_handle] if n != num]
                    if w_refs:
                        c_segs.append((" <", True))
                        c_segs.append((", ".join(str(n) for n in sorted(w_refs)), True))
                        c_segs.append((">", True))

                self.write_segments("LF-Child", c_segs)

                for cf_handle in child.get_family_handle_list():
                    cfam = self.db.get_family_from_handle(cf_handle)
                    if not cfam:
                        continue
                    cm_ev = self.get_marriage_event(cfam)
                    cm_year = self.format_date(cm_ev, year_only=True) if cm_ev else ""
                    sp_h = (
                        cfam.get_mother_handle()
                        if cfam.get_father_handle() == c_handle
                        else cfam.get_father_handle()
                    )
                    sp_p = self.db.get_person_from_handle(sp_h) if sp_h else None
                    if cm_year or sp_p:
                        m_segs = [("x", False)]
                        if cm_year:
                            m_segs.append((f" {cm_year}", False))
                        if sp_p:
                            m_segs.append((" ", False))
                            self.add_name_segments(m_segs, sp_p, abbrev_surname=False)
                        self.write_segments("LF-ChildSub", m_segs)

                if d_str:
                    self.write_line("LF-ChildSub", d_str)

                for note_txt in self.get_notes_texts(child):
                    self.write_line("LF-ChildSub", note_txt)

    def write_legend(self):
        self.write_line("LF-IndexHeader", _("ABRÉVIATIONS"))
        items = [
            ("* : né(e)", "† : décédé(e)", "x : mariage"),
            ("fs de : fils de", "fe de : fille de", "ax : date approximative"),
            ("NN : nom(s) inconnu(s)", "<n> : renvoi à la fiche n", "<n.k> : enfant k de la fiche n"),
        ]
        for row in items:
            self.write_line("LF-Body", "   |   ".join(row))

    def write_single_index(self, title, data_dict):
        if not data_dict:
            return
        self.write_line("LF-IndexHeader", title)
        for key in sorted(data_dict.keys(), key=normalize_sort_key):
            nums = sorted(data_dict[key])
            nums_str = ", ".join(str(n) for n in nums)
            self.write_segments("LF-Body", [(key, True), (f" : {nums_str}", False)])

    def write_report(self):
        self.build_entries()
        final_title = self.title_text or _("Livre des Familles")

        self.write_line("LF-Title", final_title)
        if self.subtitle_text:
            self.write_line("LF-Subtitle", self.subtitle_text)

        has_any_index = any(
            [
                self.gen_idx_surnames,
                self.gen_idx_givens,
                self.gen_idx_places,
                self.gen_idx_occus,
                self.gen_idx_spouses,
            ]
        )

        for entry in self.entries:
            self.write_entry(entry, emit_output=self.gen_repertoire)

        if self.gen_repertoire and self.include_legend:
            self.write_legend()

        if has_any_index:
            if self.gen_repertoire:
                self.doc.page_break()
            self.write_line("LF-Title", _("INDEX"))

            if self.gen_idx_surnames:
                self.write_single_index(_("Index des patronymes"), self.idx_surnames)
            if self.gen_idx_givens:
                self.write_single_index(_("Index des prénoms"), self.idx_givens)
            if self.gen_idx_places:
                self.write_single_index(_("Index des localités"), self.idx_places)
            if self.gen_idx_occus:
                self.write_single_index(_("Index des professions et fonctions"), self.idx_occus)
            if self.gen_idx_spouses:
                self.write_single_index(_("Index des épouses"), self.idx_spouses)

        self.show_completion_dialog()
