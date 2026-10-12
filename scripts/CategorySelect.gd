extends Control

signal start_game_requested(category_id: String)

@onready var card_container: GridContainer = $Margin/VBox/Scroll/CardList
@onready var search_box: LineEdit = $Margin/VBox/SearchBox
@onready var count_label: Label = $Margin/VBox/CountLabel

# Filter buttons
@onready var btn_filter_all: Button = $Margin/VBox/FilterScroll/FilterBar/FilterAll
@onready var btn_filter_physical: Button = $Margin/VBox/FilterScroll/FilterBar/FilterPhysical
@onready var btn_filter_career: Button = $Margin/VBox/FilterScroll/FilterBar/FilterCareer
@onready var btn_filter_franchise: Button = $Margin/VBox/FilterScroll/FilterBar/FilterFranchise

@onready var scores_btn: Button = $Margin/VBox/Header/TopRow/ScoresBtn
@onready var mute_btn: Button = $Margin/VBox/Header/TopRow/MuteBtn
@onready var custom_btn: Button = $Margin/VBox/Header/TopRow/CustomBtn

@onready var game_setup_modal = $GameSetupModal
@onready var filter_modal = $FilterModal
@onready var high_scores_modal = $HighScoresModal

@onready var custom_modal: Control = $CustomModal
@onready var custom_text_edit: TextEdit = $CustomModal/Panel/Margin/VBox/TextEdit
@onready var custom_status: Label = $CustomModal/Panel/Margin/VBox/StatusLabel
@onready var custom_save_btn: Button = $CustomModal/Panel/Margin/VBox/Buttons/SaveBtn
@onready var custom_close_btn: Button = $CustomModal/Panel/Margin/VBox/Buttons/CloseBtn

const CATEGORY_CARD_SCENE = preload("res://scenes/CategoryCard.tscn")

var active_filter: String = "all"
var search_query: String = ""

# Preload styles for filter pills
var style_active: StyleBoxFlat
var style_normal: StyleBoxFlat

func _ready() -> void:
	# Build styles for filter pills
	style_active = StyleBoxFlat.new()
	style_active.bg_color = Color(0.18, 0.65, 0.95, 1.0)
	style_active.set_corner_radius_all(16)

	style_normal = StyleBoxFlat.new()
	style_normal.bg_color = Color(0.14, 0.17, 0.25, 0.95)
	style_normal.set_corner_radius_all(16)

	scores_btn.pressed.connect(_open_high_scores)
	mute_btn.pressed.connect(_on_toggle_mute)
	custom_btn.pressed.connect(_open_custom_modal)
	custom_save_btn.pressed.connect(_on_save_custom_category)
	custom_close_btn.pressed.connect(_close_custom_modal)
	custom_modal.visible = false

	# Setup modal wiring
	game_setup_modal.btn_open_filter.pressed.connect(_on_open_filter_from_setup)
	game_setup_modal.start_game_confirmed.connect(_on_start_game_confirmed)
	filter_modal.filters_applied.connect(_on_filters_applied_to_setup)

	# Connect filter buttons
	btn_filter_all.pressed.connect(func(): _set_filter("all"))
	btn_filter_physical.pressed.connect(func(): _set_filter("physical"))
	btn_filter_career.pressed.connect(func(): _set_filter("career"))
	btn_filter_franchise.pressed.connect(func(): _set_filter("franchise"))

	# Connect search bar
	search_box.text_changed.connect(_on_search_changed)

	refresh_categories()

func _open_high_scores() -> void:
	AudioManager.play("click")
	high_scores_modal.open()

func _set_filter(group_id: String) -> void:
	AudioManager.play("click")
	active_filter = group_id
	_update_filter_button_styles()
	refresh_categories()

func _update_filter_button_styles() -> void:
	btn_filter_all.add_theme_stylebox_override("normal", style_active if active_filter == "all" else style_normal)
	btn_filter_physical.add_theme_stylebox_override("normal", style_active if active_filter == "physical" else style_normal)
	btn_filter_career.add_theme_stylebox_override("normal", style_active if active_filter == "career" else style_normal)
	btn_filter_franchise.add_theme_stylebox_override("normal", style_active if active_filter == "franchise" else style_normal)

func _on_search_changed(new_text: String) -> void:
	search_query = new_text.strip_edges().to_lower()
	refresh_categories()

func refresh_categories() -> void:
	for child in card_container.get_children():
		child.queue_free()

	var all_cats = CategoryLoader.get_all_categories()
	var displayed_count = 0

	for cat in all_cats:
		# 1. Filter by group
		var cat_group = cat.get("group", "")
		if active_filter != "all" and cat_group != active_filter:
			continue

		# 2. Filter by search query
		if not search_query.is_empty():
			var title_str = cat.get("title", "").to_lower()
			var prompt_str = cat.get("prompt", "").to_lower()
			var group_str = cat.get("group_label", "").to_lower()
			if not (search_query in title_str or search_query in prompt_str or search_query in group_str):
				continue

		# Instantiate card
		var card = CATEGORY_CARD_SCENE.instantiate()
		card_container.add_child(card)
		card.setup(cat)
		card.selected.connect(_on_category_selected)
		displayed_count += 1

	count_label.text = "Showing %d of %d NBA categories" % [displayed_count, all_cats.size()]

func _on_category_selected(cat_id: String) -> void:
	var cat_data = CategoryLoader.get_category(cat_id)
	game_setup_modal.open(cat_data)

func _on_open_filter_from_setup() -> void:
	AudioManager.play("click")
	filter_modal.open_with_category(
		game_setup_modal.current_category,
		game_setup_modal.selected_filters
	)

func _on_filters_applied_to_setup(filters: Dictionary) -> void:
	game_setup_modal.update_applied_filters(filters)

func _on_start_game_confirmed(cat_id: String, difficulty: String, lives: Variant, filters: Dictionary) -> void:
	GameManager.set_game_setup(cat_id, difficulty, lives, filters)
	start_game_requested.emit(cat_id)

func _on_toggle_mute() -> void:
	AudioManager.play("click")
	var is_muted = AudioManager.toggle_mute()
	mute_btn.text = "🔇 MUTED" if is_muted else "🔊 SOUND"

func _open_custom_modal() -> void:
	AudioManager.play("click")
	custom_modal.visible = true
	custom_status.text = ""
	if custom_text_edit.text.is_empty():
		var template = {
			"id": "my_nba_stat",
			"title": "My Custom NBA Stat",
			"group": "career",
			"group_label": "Custom",
			"prompt": "Which player has MORE?",
			"unit": "pts",
			"value_format": "{value} pts",
			"items": [
				{"name": "Player A", "subtext": "Team A", "value": 150},
				{"name": "Player B", "subtext": "Team B", "value": 110}
			]
		}
		custom_text_edit.text = JSON.stringify(template, "\t")

func _close_custom_modal() -> void:
	AudioManager.play("click")
	custom_modal.visible = false

func _on_save_custom_category() -> void:
	var text = custom_text_edit.text.strip_edges()
	var json = JSON.new()
	var err = json.parse(text)
	if err != OK:
		custom_status.text = "Invalid JSON: " + json.get_error_message()
		custom_status.modulate = Color(1, 0.3, 0.3)
		return

	var data = json.get_data()
	if typeof(data) != TYPE_DICTIONARY or not data.has("id") or not data.has("items"):
		custom_status.text = "Error: Must contain 'id' and 'items' array!"
		custom_status.modulate = Color(1, 0.3, 0.3)
		return

	if data["items"].size() < 2:
		custom_status.text = "Error: Must have at least 2 items to compare!"
		custom_status.modulate = Color(1, 0.3, 0.3)
		return

	var success = CategoryLoader.save_custom_category(data)
	if success:
		custom_status.text = "Category saved! Added to menu."
		custom_status.modulate = Color(0.2, 1, 0.4)
		AudioManager.play("correct")
		refresh_categories()
		await get_tree().create_timer(0.6).timeout
		custom_modal.visible = false
	else:
		custom_status.text = "Failed to save file."
		custom_status.modulate = Color(1, 0.3, 0.3)
