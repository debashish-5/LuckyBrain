from luckybrain.query_imp import QueryRewriting


class FakeModel:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def think(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def test_improve_returns_clean_query_and_skips_blank_input() -> None:
    model = FakeModel('  "Reset my account password"  ')
    rewriter = QueryRewriting(model)

    assert rewriter.improve("  how reset password??  ") == "Reset my account password"
    assert len(model.prompts) == 1
    assert rewriter.improve("   ") == ""
    assert len(model.prompts) == 1


def test_style_selects_search_or_question_prompt() -> None:
    search = QueryRewriting(FakeModel("result"))
    question = QueryRewriting(FakeModel("result"), style="question")

    assert "search query" in search._prompt("words")
    assert "well-formed question" in question._prompt("words")


def test_variants_returns_nonempty_lines_up_to_requested_count() -> None:
    model = FakeModel("- first\n\n• second\n* third")
    rewriter = QueryRewriting(model)

    assert rewriter.variants("original", n=2) == ["first", "second"]
    assert "Write 2 different" in model.prompts[0]


def test_variants_without_a_count_requests_several_and_returns_all_lines() -> None:
    model = FakeModel("first\nsecond\nthird")
    rewriter = QueryRewriting(model)

    assert rewriter.variants("original", n=None) == ["first", "second", "third"]
    assert "Write several different" in model.prompts[0]
