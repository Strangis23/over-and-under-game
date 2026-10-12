extends Control

signal filters_applied(filter_dict: Dictionary)
signal modal_closed

@onready var modal_panel: PanelContainer = $Center/Panel
@onready var title_label: Label = $Center/Panel/Margin/VBox/Header/TitleBox/Title
@onready var close_btn: Button = $Center/Panel/Margin/VBox/Header/CloseBtn

# Player sections
@onready var player_section: VBoxContainer = $Center/Panel/Margin/VBox/Scroll/Content/PlayerSection
@onready var pos_container: HBoxContainer = $Center/Panel/Margin/VBox/Scroll/Content/PlayerSection/PosContainer
@onready var decade_container: HFlowContainer = $Center/Panel/Margin/VBox/Scroll/Content/PlayerSection/DecadeContainer
@onready var status_container: HBoxContainer = $Center/Panel/Margin/VBox/Scroll/Content/PlayerSection/StatusContainer
@onready var team_dropdown: OptionButton = $Center/Panel/Margin/VBox/Scroll/Content/PlayerSection/TeamDropdown

# Team sections
@onready var team_section: VBoxContainer = $Center/Panel/Margin/VBox/Scroll/Content/TeamSection
@onready var conf_container: HBoxContainer = $Center/Panel/Margin/VBox/Scroll/Content/TeamSection/ConfContainer

# Footer
@onready var match_count_lbl: Label = $Center/Panel/Margin/VBox/Footer/MatchCountLabel
@onready var reset_btn: Button = $Center/Panel/Margin/VBox/Footer/BtnBox/ResetBtn
@onready var apply_btn: Button = $Center/Panel/Margin/VBox/Footer/BtnBox/ApplyBtn

const NBA_TEAMS = [
	"All Teams",
	"Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
	"Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
	"Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
	"LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
	"Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
	"Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns",
	"Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors",
	"Utah Jazz", "Washington Wizards"
]

var current_category: Dictionary = {}
var raw_items: Array = []
var active_filters: Dictionary = {
	"position": "All",
	"decade": "All",
	"status": "All",
	"team": "All",
	"conference": "All"
}

func _ready() -> void:
	visible = false
	close_btn.pressed.connect(_on_close_pressed)
	reset_btn.pressed.connect(_on_reset_pressed)
	apply_btn.pressed.connect(_on_apply_pressed)

	_setup_team_dropdown()
	_connect_chips(pos_container, "position")
	_connect_chips(decade_container, "decade")
	_connect_chips(status_container, "status")
	_connect_chips(conf_container, "conference")

func _setup_team_dropdown() -> void:
	team_dropdown.clear()
	for team in NBA_TEAMS:
		team_dropdown.add_item(team)
	team_dropdown.item_selected.connect(_on_team_selected)

func open_with_category(cat_data: Dictionary, existing_filters: Dictionary) -> void:
	current_category = cat_data
	raw_items = cat_data.get("items", [])
	active_filters = existing_filters.duplicate()

	var filter_type = cat_data.get("filter_type", "player")
	if filter_type == "team":
		player_section.visible = false
		team_section.visible = true
	else:
		player_section.visible = true
		team_section.visible = false

	# Refresh UI selections
	_update_chip_styles(pos_container, active_filters.get("position", "All"))
	_update_chip_styles(decade_container, active_filters.get("decade", "All"))
	_update_chip_styles(status_container, active_filters.get("status", "All"))
	_update_chip_styles(conf_container, active_filters.get("conference", "All"))

	var team_name = active_filters.get("team", "All")
	var idx = 0
	for i in range(team_dropdown.item_count):
		if team_dropdown.get_item_text(i) == team_name or (team_name == "All" and i == 0):
			idx = i
			break
	team_dropdown.selected = idx

	_recalculate_matches()

	# Open animation
	visible = true
	modal_panel.scale = Vector2(0.85, 0.85)
	modal_panel.modulate.a = 0.0
	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(modal_panel, "scale", Vector2.ONE, 0.25)
	tween.tween_property(modal_panel, "modulate:a", 1.0, 0.2)

func _connect_chips(parent: Container, filter_key: String) -> void:
	for child in parent.get_children():
		if child is Button:
			child.pressed.connect(func():
				var val = child.get_meta("filter_value", child.text)
				active_filters[filter_key] = val
				_update_chip_styles(parent, val)
				_recalculate_matches()
			)

func _update_chip_styles(parent: Container, active_val: String) -> void:
	for child in parent.get_children():
		if child is Button:
			var val = child.get_meta("filter_value", child.text)
			var is_selected = (val == active_val) or (active_val == "All" and (val == "All" or val == "All Positions" or val == "All Eras" or val == "All Players" or val == "All Conferences"))
			if is_selected:
				child.self_modulate = Color(0.15, 0.85, 1.0, 1.0) # Vibrant highlight
			else:
				child.self_modulate = Color(0.65, 0.72, 0.85, 0.8)

func _on_team_selected(index: int) -> void:
	var selected_text = team_dropdown.get_item_text(index)
	if index == 0 or selected_text == "All Teams":
		active_filters["team"] = "All"
	else:
		active_filters["team"] = selected_text
	_recalculate_matches()

func _recalculate_matches() -> void:
	var count = 0
	for item in raw_items:
		if _matches_filters(item, active_filters):
			count += 1

	if count >= 2:
		match_count_lbl.text = "✅ %d matching candidates ready for duels" % count
		match_count_lbl.add_theme_color_override("font_color", Color(0.3, 0.95, 0.5, 1))
		apply_btn.disabled = false
		apply_btn.text = "Apply Filters (%d)" % count
	elif count == 1:
		match_count_lbl.text = "⚠️ Only 1 candidate matches! Need at least 2."
		match_count_lbl.add_theme_color_override("font_color", Color(1.0, 0.5, 0.2, 1))
		apply_btn.disabled = true
		apply_btn.text = "Apply Filters"
	else:
		match_count_lbl.text = "❌ 0 candidates match! Broaden your criteria."
		match_count_lbl.add_theme_color_override("font_color", Color(1.0, 0.3, 0.3, 1))
		apply_btn.disabled = true
		apply_btn.text = "Apply Filters"

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
			# Check nickname e.g. "Lakers"
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

func _on_reset_pressed() -> void:
	AudioManager.play("click")
	active_filters = {
		"position": "All",
		"decade": "All",
		"status": "All",
		"team": "All",
		"conference": "All"
	}
	_update_chip_styles(pos_container, "All")
	_update_chip_styles(decade_container, "All")
	_update_chip_styles(status_container, "All")
	_update_chip_styles(conf_container, "All")
	team_dropdown.selected = 0
	_recalculate_matches()

func _on_apply_pressed() -> void:
	AudioManager.play("click")
	visible = false
	filters_applied.emit(active_filters)

func _on_close_pressed() -> void:
	AudioManager.play("click")
	visible = false
	modal_closed.emit()
