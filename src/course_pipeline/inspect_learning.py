from __future__ import annotations

import curses
import json
from dataclasses import dataclass
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@dataclass
class CourseLearningView:
    course_id: str
    course_title: str
    coverage_notes: dict
    learning_outcomes: list[dict]


def load_learning_run(run_dir: Path) -> list[CourseLearningView]:
    rows = _read_jsonl(run_dir / "learning_outcomes.jsonl")
    views = []
    for row in rows:
        views.append(
            CourseLearningView(
                course_id=row["course_id"],
                course_title=row["course_title"],
                coverage_notes=row.get("coverage_notes", {}),
                learning_outcomes=row.get("learning_outcomes", []),
            )
        )
    return views


class LearningInspector:
    def __init__(self, stdscr, run_dir: Path) -> None:
        self.stdscr = stdscr
        self.run_dir = run_dir
        self.courses = load_learning_run(run_dir)
        self.course_index = 0
        self.scroll = 0

    def current_course(self) -> CourseLearningView:
        return self.courses[self.course_index]

    def current_items(self) -> list[str]:
        course = self.current_course()
        items = []
        notes = course.coverage_notes or {}
        items.append(
            "coverage: "
            f"syllabus_present={notes.get('syllabus_present')} "
            f"evidence_strength={notes.get('evidence_strength')}"
        )
        for gap in notes.get("gaps_or_ambiguities", []):
            items.append(f"gap: {gap}")
        for outcome in course.learning_outcomes:
            items.append(
                f"{outcome['id']} | {outcome['knowledge_type']} | {outcome['process_level']} | "
                f"DOK {outcome['dok_level']} | {outcome['solo_level']} | conf={outcome['confidence']}"
            )
            items.append(f"claim: {outcome['claim']}")
            items.append(f"why: {outcome['reasoning']}")
            for citation in outcome.get("citations", []):
                items.append(f"cite: {citation['field']} -> {citation['evidence']}")
            items.append("")
        return items

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.keypad(True)
        while True:
            self.draw()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                return
            if key in (curses.KEY_UP, ord("k")):
                self.scroll = max(0, self.scroll - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                items = self.current_items()
                max_scroll = max(0, len(items) - max(1, curses.LINES - 4))
                self.scroll = min(max_scroll, self.scroll + 1)
            elif key == ord("n"):
                self.course_index = min(len(self.courses) - 1, self.course_index + 1)
                self.scroll = 0
            elif key == ord("p"):
                self.course_index = max(0, self.course_index - 1)
                self.scroll = 0

    def draw(self) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if not self.courses:
            self.stdscr.addnstr(0, 0, f"No learning_outcomes.jsonl found in {self.run_dir}", width - 1)
            self.stdscr.refresh()
            return
        course = self.current_course()
        header = (
            f"Run: {self.run_dir.name} | Course {self.course_index + 1}/{len(self.courses)} | "
            f"{course.course_id} - {course.course_title}"
        )
        self.stdscr.addnstr(0, 0, header, width - 1, curses.A_BOLD)
        self.stdscr.addnstr(1, 0, "q quit | n/p next-prev course | j/k scroll", width - 1)

        items = self.current_items()
        visible_height = max(1, height - 3)
        for row, item in enumerate(items[self.scroll : self.scroll + visible_height], start=2):
            self.stdscr.addnstr(row, 0, item, width - 1)

        self.stdscr.refresh()


def launch_learning_inspector(run_dir: Path) -> None:
    curses.wrapper(lambda stdscr: LearningInspector(stdscr, run_dir).run())
