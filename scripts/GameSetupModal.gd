extends Control

signal start_game_confirmed(category_id: String, difficulty: String, lives_mode: Variant, filters: Dictionary)
signal modal_closed

@onready var modal_panel: PanelContainer = $Center/Panel
@onready var cat_title_label: Label = $Center/Panel/Margin/VBox/Header/TitleBox/CatTitle
@onready var cat_prompt_label: Label = $Center/Panel/Margin/VBox/Header/TitleBox/CatPrompt
@onready var close_btn: Button = $Center/Panel/Margin/VBox/Header/CloseBtn

# Difficulty buttons
@onready var btn_diff_easy: Button = $Center/Panel/Margin/VBox/Content/DiffSection/DiffBox/DiffEasy
@onready var btn_diff_med: Button = $Center/Panel/Margin/VBox/Content/DiffSection/DiffBox/DiffMedium
@onready var btn_diff_hard: Button = $Center/Panel/Margin/VBox/Content/DiffSection/DiffBox/DiffHard

# Lives buttons
@onready var btn_lives_1: Button = $Center/Panel/Margin/VBox/Content/LivesSection/LivesBox/Lives1
@onready var btn_lives_3: Button = $Center/Panel/Margin/VBox/Content/LivesSection/LivesBox/Lives3
@onready var btn_lives_5: Button = $Center/Panel/Margin/VBox/Content/LivesSection/LivesBox/Lives5
@onready var btn_lives_free: Button = $Center/Panel/Margin/VBox/Content/LivesSection/LivesBox/LivesFree
@onready var free_play_note: Label = $Center/Panel/Margin/VBox/Content/LivesSection/FreePlayNote

# Filter section
@onready var btn_open_filter: Button = $Center/Panel/Margin/VBox/Content/FilterSection/FilterRow/FilterBtn
@onready var filter_summary_label: Label = $Center/Panel/Margin/VBox/Content/FilterSection/FilterSummary
@onready var btn_reset_filter: Button = $Center/Panel/Margin/VBox/Content/FilterSection/FilterRow/ResetFilterBtn

# Pool count & Start
@onready var pool_status_label: Label = $Center/Panel/Margin/VBox/Footer/PoolStatusLabel
@onready var start_btn: Button = $Center/Panel/Margin/VBox/Footer/BtnRow/StartBtn
@onready var cancel_btn: Button = $Center/Panel/Margin/VBox/Footer/BtnRow/CancelBtn

var current_category: Dictionary = {}
var raw_items: Array = []

var selected_difficulty: String = "easy" # "easy", "medium", "hard"
var selected_lives: Variant = 3          # 1, 3, 5, or "free_play"
var selected_filters: Dictionary = {
	"position": "All",
	"decade": "All",
	"status": "All",
	"team": "All",
	"conference": "All"
}

# Pill styles
var style_active: StyleBoxFlat
var style_inactive: StyleBoxFlat
var style_free_play_active: StyleBoxFlat

func _ready() -> void:
	visible = false

	# Setup styles
	style_active = StyleBoxFlat.new()
	style_active.bg_color = Color(0.18, 0.65, 0.95, 1.0)
	style_active.set_corner_radius_all(14)
	style_active.border_color = Color(1, 1, 1, 0.85)
	style_active.set_border_width_all(2)

	style_inactive = StyleBoxFlat.new()
	style_inactive.bg_color = Color(0.13, 0.16, 0.24, 0.95)
	style_inactive.set_corner_radius_all(14)
	style_inactive.border_color = Color(0.24, 0.3, 0.44, 0.7)
	style_inactive.set_border_width_all(1)

	style_free_play_active = StyleBoxFlat.new()
	style_free_play_active.bg_color = Color(0.85, 0.6, 0.1, 1.0)
	style_free_play_active.set_corner_radius_all(14)
	style_free_play_active.border_color = Color(1, 1, 0.7, 0.9)
	style_free_play_active.set_border_width_all(2)

	close_btn.pressed.connect(_on_close_pressed)
	cancel_btn.pressed.connect(_on_close_pressed)
	start_btn.pressed.connect(_on_start_pressed)

	btn_diff_easy.pressed.connect(func(): _set_difficulty("easy"))
	btn_diff_med.pressed.connect(func(): _set_difficulty("medium"))
	btn_diff_hard.pressed.connect(func(): _set_difficulty("hard"))

	btn_lives_1.pressed.connect(func(): _set_lives(1))
	btn_lives_3.pressed.connect(func(): _set_lives(3))
	btn_lives_5.pressed.connect(func(): _set_lives(5))
	btn_lives_free.pressed.connect(func(): _set_lives("free_play"))

	btn_reset_filter.pressed.connect(_on_reset_filter_pressed)

func open(category_data: Dictionary) -> void:
	current_category = category_data
	raw_items = category_data.get("items", [])
	
	cat_title_label.text = category_data.get("title", "Category")
	cat_prompt_label.text = category_data.get("prompt", "Who has more?").to_upper()

	# Defaults
	selected_difficulty = "easy"
	selected_lives = 3
	selected_filters = {
		"position": "All",
		"decade": "All",
		"status": "All",
		"team": "All",
		"conference": "All"
	}

	_update_ui()

	# Entrance animation
	visible = true
	modal_panel.scale = Vector2(0.85, 0.85)
	modal_panel.modulate.a = 0.0
	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(modal_panel, "scale", Vector2.ONE, 0.25)
	tween.tween_property(modal_panel, "modulate:a", 1.0, 0.2)

func _set_difficulty(diff: String) -> void:
	AudioManager.play("click")
	selected_difficulty = diff
	_update_ui()

func _set_lives(lives: Variant) -> void:
	AudioManager.play("click")
	selected_lives = lives
	_update_ui()

func update_applied_filters(new_filters: Dictionary) -> void:
	selected_filters = new_filters.duplicate()
	_update_ui()

func _on_reset_filter_pressed() -> void:
	AudioManager.play("click")
	selected_filters = {
		"position": "All",
		"decade": "All",
		"status": "All",
		"team": "All",
		"conference": "All"
	}
	_update_ui()

func _update_ui() -> void:
	# Difficulty buttons
	btn_diff_easy.add_theme_stylebox_override("normal", style_active if selected_difficulty == "easy" else style_inactive)
	btn_diff_med.add_theme_stylebox_override("normal", style_active if selected_difficulty == "medium" else style_inactive)
	btn_diff_hard.add_theme_stylebox_override("normal", style_active if selected_difficulty == "hard" else style_inactive)

	# Lives buttons
	btn_lives_1.add_theme_stylebox_override("normal", style_active if str(selected_lives) == "1" else style_inactive)
	btn_lives_3.add_theme_stylebox_override("normal", style_active if str(selected_lives) == "3" else style_inactive)
	btn_lives_5.add_theme_stylebox_override("normal", style_active if str(selected_lives) == "5" else style_inactive)
	btn_lives_free.add_theme_stylebox_override("normal", style_free_play_active if str(selected_lives) == "free_play" else style_inactive)

	free_play_note.visible = (str(selected_lives) == "free_play")

	# Filter summary
	var active_parts: Array = []
	if selected_filters.get("position", "All") != "All":
		active_parts.append(selected_filters["position"])
	if selected_filters.get("decade", "All") != "All":
		active_parts.append(selected_filters["decade"])
	if selected_filters.get("status", "All") != "All":
		active_parts.append(selected_filters["status"])
	if selected_filters.get("team", "All") != "All":
		active_parts.append(selected_filters["team"])
	if selected_filters.get("conference", "All") != "All":
		active_parts.append(selected_filters["conference"])

	if active_parts.is_empty():
		filter_summary_label.text = "🎯 All Contenders (no filters applied)"
		filter_summary_label.add_theme_color_override("font_color", Color(0.65, 0.72, 0.85, 1))
		btn_reset_filter.visible = false
	else:
		filter_summary_label.text = "🎯 " + " • ".join(active_parts)
		filter_summary_label.add_theme_color_override("font_color", Color(0.3, 0.9, 1, 1))
		btn_reset_filter.visible = true

	# Calculate pool size
	var filtered_matches = _count_filter_matches()
	var final_pool_size = _calculate_difficulty_pool_size(filtered_matches)

	var pct_str = "Top 30%" if selected_difficulty == "easy" else ("Top 60%" if selected_difficulty == "medium" else "100%")
	
	if final_pool_size >= 2:
		pool_status_label.text = "⚔️ Pool: %d contenders ready (%s of %d matching)" % [final_pool_size, pct_str, filtered_matches]
		pool_status_label.add_theme_color_override("font_color", Color(0.3, 0.95, 0.5, 1))
		start_btn.disabled = false
	else:
		pool_status_label.text = "⚠️ Pool has %d contenders! Need at least 2 (try Medium/Hard or reset filters)." % final_pool_size
		pool_status_label.add_theme_color_override("font_color", Color(1.0, 0.4, 0.3, 1))
		start_btn.disabled = true

func _count_filter_matches() -> int:
	var count = 0
	for item in raw_items:
		if _matches_filters(item, selected_filters):
			count += 1
	return count

func _calculate_difficulty_pool_size(total_filtered: int) -> int:
	if total_filtered <= 0:
		return 0
	if selected_difficulty == "easy":
		return maxi(2, int(ceil(total_filtered * 0.3))) if total_filtered >= 2 else total_filtered
	elif selected_difficulty == "medium":
		return maxi(2, int(ceil(total_filtered * 0.6))) if total_filtered >= 2 else total_filtered
	else:
		return total_filtered

func _matches_filters(item: Dictionary, filters: Dictionary) -> bool:
	# 1. Position filter
	var pos_f = filters.get("position", "All")
	if pos_f != "All":
		var positions: Array = item.get("positions", [item.get("position", "")])
		if not positions.has(pos_f) and not pos_f in item.get("position", ""):
			return false

	# 2. Decade filter
	var dec_f = filters.get("decade", "All")
	if dec_f != "All":
		var decades: Array = item.get("decades", [])
		if not decades.has(dec_f):
			return false

	# 3. Status filter
	var st_f = filters.get("status", "All")
	if st_f != "All":
		var status: String = item.get("status", "")
		if st_f == "Active Only" and status != "Active":
			return false
		elif st_f == "Legends Only" and status != "Retired":
			return false

	# 4. Team filter
	var team_f = filters.get("team", "All")
	if team_f != "All":
		var item_team = item.get("team", "")
		var item_team_full = item.get("team_full", "")
		var subtext = item.get("subtext", "")
		var matched = false
		if team_f in item_team_full or team_f in item_team or team_f in subtext:
			matched = true
		else:
			var parts = team_f.split(" ")
			var nick = parts[parts.size() - 1]
			if nick in item_team or nick in subtext:
				matched = true
		if not matched:
			return false

	# 5. Conference filter
	var conf_f = filters.get("conference", "All")
	if conf_f != "All":
		var item_conf = item.get("conference", "")
		if not conf_f.begins_with(item_conf) and not item_conf.begins_with(conf_f):
			return false

	return true

func _on_start_pressed() -> void:
	AudioManager.play("click")
	visible = false
	start_game_confirmed.emit(
		current_category.get("id", ""),
		selected_difficulty,
		selected_lives,
		selected_filters
	)

func _on_close_pressed() -> void:
	AudioManager.play("click")
	visible = false
	modal_closed.emit()
