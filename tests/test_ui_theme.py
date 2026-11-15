import ui_theme


def test_theme_components_escape_untrusted_text(monkeypatch):
    rendered = []
    monkeypatch.setattr(
        ui_theme.st,
        "markdown",
        lambda body, **kwargs: rendered.append((body, kwargs)),
    )

    ui_theme.render_hero("<script>", "Flame", "Freefall", "<unsafe>", ["<detail>"])
    ui_theme.render_kpi("<label>", 42, "<icon>")
    ui_theme.render_research_card("<title>", "<finding>", "<source>")

    assert len(rendered) == 3
    for markup, options in rendered:
        assert options["unsafe_allow_html"] is True
        assert "<script>" not in markup
        assert "<unsafe>" not in markup
        assert "<detail>" not in markup
        assert "<label>" not in markup
        assert "<icon>" not in markup
        assert "<title>" not in markup
        assert "<finding>" not in markup
        assert "<source>" not in markup


def test_theme_components_render_supplied_values(monkeypatch):
    rendered = []
    monkeypatch.setattr(
        ui_theme.st,
        "markdown",
        lambda body, **kwargs: rendered.append(body),
    )

    ui_theme.render_hero("NASA RESEARCH", "Flame in", "Freefall", "Explore the data", ["5 investigations"])
    ui_theme.render_kpi("Investigations", 5, "science")
    ui_theme.render_research_card("PSI-10 finding", "Observed finding text", "Source: paper, p. 3")

    markup = "\n".join(rendered)
    assert "NASA RESEARCH" in markup
    assert "5 investigations" in markup
    assert "Investigations" in markup
    assert ">5<" in markup
    assert "Observed finding text" in markup
    assert "Source: paper, p. 3" in markup
