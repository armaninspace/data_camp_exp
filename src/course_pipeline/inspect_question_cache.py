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
class CourseCacheView:
    course_id: str
    groups: list[dict]


def load_question_cache_run(run_dir: Path) -> list[CourseCacheView]:
    groups = _read_jsonl(run_dir / "claim_question_groups.jsonl")
    variations = _read_jsonl(run_dir / "question_group_variations.jsonl")
    answers = _read_jsonl(run_dir / "canonical_answers.jsonl")
    variations_by_group: dict[str, list[dict]] = {}
    answers_by_group: dict[str, list[dict]] = {}
    for row in variations:
        variations_by_group.setdefault(row["question_group_id"], []).append(row)
    for row in answers:
        answers_by_group.setdefault(row["question_group_id"], []).append(row)

    groups_by_course: dict[str, list[dict]] = {}
    for group in groups:
        groups_by_course.setdefault(group["course_id"], []).append(
            {
                **group,
                "variations": sorted(
                    variations_by_group.get(group["question_group_id"], []),
                    key=lambda row: row["normalized_text"],
                ),
                "answers": answers_by_group.get(group["question_group_id"], []),
            }
        )
    return [CourseCacheView(course_id=course_id, groups=rows) for course_id, rows in sorted(groups_by_course.items())]


class QuestionCacheInspector:
    def __init__(self, stdscr, run_dir: Path) -> None:
        self.stdscr = stdscr
        self.run_dir = run_dir
        self.courses = load_question_cache_run(run_dir)
        self.course_index = 0
        self.scroll = 0

    def current_course(self) -> CourseCacheView:
        return self.courses[self.course_index]

    def current_items(self) -> list[str]:
        course = self.current_course()
        items: list[str] = []
        for group in course.groups:
            items.append(
                f"{group['claim_id']} | {group['intent_slug']} | conf={group['confidence']} | "
                f"{group['canonical_question']}"
            )
            for answer in group.get("answers", []):
                items.append(f"answer: {answer['answer_markdown']}")
            for variation in group.get("variations", []):
                items.append(f"var: {variation['text']}")
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
                max_scroll = max(0, len(items) - max(1, curses.LINES - 3))
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
            self.stdscr.addnstr(0, 0, f"No question-cache artifacts found in {self.run_dir}", width - 1)
            self.stdscr.refresh()
            return
        course = self.current_course()
        header = f"Run: {self.run_dir.name} | Course {self.course_index + 1}/{len(self.courses)} | {course.course_id}"
        self.stdscr.addnstr(0, 0, header, width - 1, curses.A_BOLD)
        self.stdscr.addnstr(1, 0, "q quit | n/p next-prev course | j/k scroll", width - 1)
        items = self.current_items()
        visible_height = max(1, height - 2)
        for row, item in enumerate(items[self.scroll : self.scroll + visible_height], start=2):
            self.stdscr.addnstr(row, 0, item, width - 1)
        self.stdscr.refresh()


def launch_question_cache_inspector(run_dir: Path) -> None:
    curses.wrapper(lambda stdscr: QuestionCacheInspector(stdscr, run_dir).run())
