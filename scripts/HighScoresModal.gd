extends Control

signal modal_closed

@onready var modal_panel: PanelContainer = $Center/Panel
@onready var close_btn: Button = $Center/Panel/Margin/VBox/Header/CloseBtn

# Stat summary
@onready var stat_best: Label = $Center/Panel/Margin/VBox/StatsBanner/BestCard/VBox/Value
@onready var stat_games: Label = $Center/Panel/Margin/VBox/StatsBanner/GamesCard/VBox/Value
@onready var stat_accuracy: Label = $Center/Panel/Margin/VBox/StatsBanner/AccuracyCard/VBox/Value

# Filters
@onready var category_dropdown: OptionButton = $Center/Panel/Margin/VBox/Filters/CatDropdown
@onready var diff_container: HBoxContainer = $Center/Panel/Margin/VBox/Filters/DiffRow/DiffContainer
@onready var lives_container: HBoxContainer = $Center/Panel/Margin/VBox/Filters/LivesRow/LivesContainer

# List & Empty state
@onready var score_list_container: VBoxContainer = $Center/Panel/Margin/VBox/Scroll/ScoreList
@onready var empty_state: VBoxContainer = $Center/Panel/Margin/VBox/Scroll/EmptyState
@onready var clear_btn: Button = $Center/Panel/Margin/VBox/Footer/ClearBtn
@onready var back_btn: Button = $Center/Panel/Margin/VBox/Footer/BackBtn

var selected_category_filter: String = "All"
var selected_diff_filter: String = "All"
var selected_lives_filter: String = "All"

# Styles for filter chips
var chip_style_active: StyleBoxFlat
var chip_style_inactive: StyleBoxFlat

func _ready() -> void:
	visible = false

	chip_style_active = StyleBoxFlat.new()
	chip_style_active.bg_color = Color(0.18, 0.65, 0.95, 1.0)
	chip_style_active.set_corner_radius_all(12)
	chip_style_active.border_color = Color(1, 1, 1, 0.8)
	chip_style_active.set_border_width_all(1)

	chip_style_inactive = StyleBoxFlat.new()
	chip_style_inactive.bg_color = Color(0.12, 0.15, 0.22, 0.9)
	chip_style_inactive.set_corner_radius_all(12)
	chip_style_inactive.border_color = Color(0.24, 0.3, 0.44, 0.6)
	chip_style_inactive.set_border_width_all(1)

	close_btn.pressed.connect(_on_close_pressed)
	back_btn.pressed.connect(_on_close_pressed)
	clear_btn.pressed.connect(_on_clear_pressed)

	_setup_category_dropdown()
	_setup_filter_chips(diff_container, "diff")
	_setup_filter_chips(lives_container, "lives")

func _setup_category_dropdown() -> void:
	category_dropdown.clear()
	category_dropdown.add_item("⭐ All Categories")
	var all_cats = CategoryLoader.get_all_categories()
	for cat in all_cats:
		category_dropdown.add_item(cat.get("title", ""))
	category_dropdown.item_selected.connect(_on_category_filter_selected)

func _setup_filter_chips(container: Container, filter_type: String) -> void:
	for child in container.get_children():
		if child is Button:
			child.pressed.connect(func():
				var val = child.get_meta("filter_value", child.text)
				if filter_type == "diff":
					selected_diff_filter = val
					_update_chips_visual(diff_container, selected_diff_filter)
				elif filter_type == "lives":
					selected_lives_filter = val
					_update_chips_visual(lives_container, selected_lives_filter)
				AudioManager.play("click")
				_refresh_scores_display()
			)

func _update_chips_visual(container: Container, active_val: String) -> void:
	for child in container.get_children():
		if child is Button:
			var val = child.get_meta("filter_value", child.text)
			child.add_theme_stylebox_override("normal", chip_style_active if val == active_val else chip_style_inactive)

func open() -> void:
	_update_stats_banner()
	_update_chips_visual(diff_container, selected_diff_filter)
	_update_chips_visual(lives_container, selected_lives_filter)
	_refresh_scores_display()

	visible = true
	modal_panel.scale = Vector2(0.85, 0.85)
	modal_panel.modulate.a = 0.0
	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(modal_panel, "scale", Vector2.ONE, 0.25)
	tween.tween_property(modal_panel, "modulate:a", 1.0, 0.2)

func _update_stats_banner() -> void:
	# Compute all-time best
	var overall_best = 0
	for entry in GameManager.high_scores:
		if entry.get("score", 0) > overall_best:
			overall_best = entry.get("score", 0)
	stat_best.text = "🔥 %d" % overall_best
	stat_games.text = "🎮 %d" % GameManager.total_games_played

	var acc = 0.0
	if GameManager.total_guesses > 0:
		acc = (float(GameManager.total_correct) / float(GameManager.total_guesses)) * 100.0
	stat_accuracy.text = "🎯 %.1f%%" % acc

func _on_category_filter_selected(index: int) -> void:
	AudioManager.play("click")
	if index == 0:
		selected_category_filter = "All"
	else:
		selected_category_filter = category_dropdown.get_item_text(index)
	_refresh_scores_display()

func _refresh_scores_display() -> void:
	for child in score_list_container.get_children():
		child.queue_free()

	var scores = GameManager.get_filtered_high_scores(
		selected_category_filter,
		selected_diff_filter,
		selected_lives_filter
	)

	if scores.is_empty():
		empty_state.visible = true
		score_list_container.visible = false
	else:
		empty_state.visible = false
		score_list_container.visible = true
		var rank = 1
		for entry in scores:
			var card = _create_score_card(rank, entry)
			score_list_container.add_child(card)
			rank += 1

func _create_score_card(rank: int, entry: Dictionary) -> PanelContainer:
	var panel = PanelContainer.new()
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.1, 0.13, 0.2, 0.95)
	style.set_corner_radius_all(14)
	style.set_border_width_all(1)
	
	if rank == 1:
		style.border_color = Color(1.0, 0.85, 0.2, 0.9)
		style.bg_color = Color(0.14, 0.16, 0.12, 0.95)
	elif rank == 2:
		style.border_color = Color(0.8, 0.85, 0.9, 0.8)
	elif rank == 3:
		style.border_color = Color(0.8, 0.5, 0.2, 0.8)
	else:
		style.border_color = Color(0.2, 0.26, 0.38, 0.6)

	panel.add_theme_stylebox_override("panel", style)

	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 14)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_right", 14)
	margin.add_theme_constant_override("margin_bottom", 10)
	panel.add_child(margin)

	var hbox = HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 14)
	margin.add_child(hbox)

	# Rank badge
	var rank_label = Label.new()
	rank_label.custom_minimum_size = Vector2(36, 0)
	var rank_str = "#%d" % rank
	if rank == 1: rank_str = "🥇"
	elif rank == 2: rank_str = "🥈"
	elif rank == 3: rank_str = "🥉"
	rank_label.text = rank_str
	rank_label.add_theme_font_size_override("font_size", 20 if rank <= 3 else 16)
	rank_label.add_theme_color_override("font_color", Color(1, 0.85, 0.3) if rank == 1 else Color(0.8, 0.85, 0.95))
	hbox.add_child(rank_label)

	# Score display
	var score_box = VBoxContainer.new()
	score_box.custom_minimum_size = Vector2(50, 0)
	var score_val = Label.new()
	score_val.text = "%d" % entry.get("score", 0)
	score_val.add_theme_font_size_override("font_size", 24)
	score_val.add_theme_color_override("font_color", Color(1, 0.55, 0.1, 1))
	score_box.add_child(score_val)
	
	var streak_sub = Label.new()
	streak_sub.text = "streak"
	streak_sub.add_theme_font_size_override("font_size", 10)
	streak_sub.add_theme_color_override("font_color", Color(0.5, 0.6, 0.75, 1))
	score_box.add_child(streak_sub)
	hbox.add_child(score_box)

	# Details (Category & settings pills)
	var details = VBoxContainer.new()
	details.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details.add_theme_constant_override("separation", 4)
	
	var cat_title = Label.new()
	cat_title.text = entry.get("category_title", "Category")
	cat_title.add_theme_font_size_override("font_size", 15)
	cat_title.add_theme_color_override("font_color", Color(1, 1, 1, 1))
	details.add_child(cat_title)

	var pills_row = HBoxContainer.new()
	pills_row.add_theme_constant_override("separation", 8)

	var diff_chip = Label.new()
	diff_chip.text = " %s " % entry.get("difficulty", "Normal")
	diff_chip.add_theme_font_size_override("font_size", 11)
	diff_chip.add_theme_color_override("font_color", Color(0.3, 0.9, 1, 1))
	pills_row.add_child(diff_chip)

	var lives_chip = Label.new()
	lives_chip.text = " %s " % entry.get("lives", "3 Lives")
	lives_chip.add_theme_font_size_override("font_size", 11)
	lives_chip.add_theme_color_override("font_color", Color(1, 0.4, 0.5, 1))
	pills_row.add_child(lives_chip)

	if entry.has("filters") and entry.get("filters") != "All Contenders":
		var f_chip = Label.new()
		f_chip.text = " ⚙️ %s " % entry.get("filters")
		f_chip.add_theme_font_size_override("font_size", 11)
		f_chip.add_theme_color_override("font_color", Color(0.6, 0.8, 0.6, 1))
		pills_row.add_child(f_chip)

	details.add_child(pills_row)
	hbox.add_child(details)

	# Date
	var date_lbl = Label.new()
	date_lbl.text = entry.get("date", "")
	date_lbl.add_theme_font_size_override("font_size", 12)
	date_lbl.add_theme_color_override("font_color", Color(0.45, 0.52, 0.65, 1))
	hbox.add_child(date_lbl)

	return panel

func _on_clear_pressed() -> void:
	AudioManager.play("click")
	GameManager.clear_high_scores()
	_update_stats_banner()
	_refresh_scores_display()

func _on_close_pressed() -> void:
	AudioManager.play("click")
	visible = false
	modal_closed.emit()
