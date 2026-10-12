extends Control

signal return_to_menu_requested

@onready var back_btn: Button = $Margin/VBox/TopBar/BackBtn
@onready var category_title_lbl: Label = $Margin/VBox/TopBar/CategoryTitle

# Lives display
@onready var lives_box: HBoxContainer = $Margin/VBox/TopBar/LivesBox
@onready var heart_nodes: Array[TextureRect] = [
	$Margin/VBox/TopBar/LivesBox/Heart1,
	$Margin/VBox/TopBar/LivesBox/Heart2,
	$Margin/VBox/TopBar/LivesBox/Heart3,
	$Margin/VBox/TopBar/LivesBox/Heart4,
	$Margin/VBox/TopBar/LivesBox/Heart5
]
@onready var free_play_icon: TextureRect = $Margin/VBox/TopBar/LivesBox/FreePlayIcon
@onready var free_play_label: Label = $Margin/VBox/TopBar/LivesBox/FreePlayLabel

# Streak & prompt
@onready var streak_lbl: Label = $Margin/VBox/TopBar/StreakBox/ScoreLabel
@onready var best_lbl: Label = $Margin/VBox/TopBar/StreakBox/BestLabel
@onready var prompt_lbl: Label = $Margin/VBox/PromptBanner/PromptLabel

@onready var active_filters_bar: PanelContainer = $Margin/VBox/ActiveFiltersBar
@onready var active_filter_label: Label = $Margin/VBox/ActiveFiltersBar/Margin/HBox/ActiveFilterLabel

@onready var duel_card = $Margin/VBox/CardStage/DuelCard
@onready var game_over_modal = $GameOverModal
@onready var feedback_banner = $FeedbackBanner
@onready var feedback_label = $FeedbackBanner/Margin/Label

@onready var btn_swipe_left: Button = $Margin/VBox/BottomControls/SwipeLeftBtn
@onready var btn_swipe_right: Button = $Margin/VBox/BottomControls/SwipeRightBtn

const BALL_FULL = preload("res://assets/icons/basketball.png")
const BALL_EMPTY = preload("res://assets/icons/basketball_empty.png")
const PREFETCH_SETS_AHEAD: int = 5

const BASKETBALL_CORRECT_PHRASES = [
	"SWISH! 🏀",
	"BUCKET! 🔥",
	"AND-ONE! 💪",
	"CLUTCH! ⚡",
	"SPLASH! 💦",
	"FROM DOWNTOWN! 🎯"
]

const BASKETBALL_WRONG_PHRASES = [
	"TURNOVER! ⚠️ -1 🏀",
	"BRICK! 🧱 -1 🏀",
	"AIRBALL! 💨 -1 🏀",
	"OFF THE RIM! ❌ -1 🏀"
]

var current_category: Dictionary = {}
var raw_category_items: Array = []
var items_pool: Array = []
var upcoming_duels: Array = []
var current_left_item: Dictionary = {}
var current_right_item: Dictionary = {}
var recent_names: Array = []

func _ready() -> void:
	back_btn.pressed.connect(_on_back_pressed)
	btn_swipe_left.pressed.connect(_on_manual_pick_left)
	btn_swipe_right.pressed.connect(_on_manual_pick_right)
	duel_card.choice_made.connect(_on_choice_made)

	game_over_modal.retry_pressed.connect(_on_retry_pressed)
	game_over_modal.change_category_pressed.connect(_on_back_pressed)

	GameManager.score_changed.connect(_on_score_changed)
	GameManager.game_over_triggered.connect(_on_game_over)

	feedback_banner.visible = false
	active_filters_bar.visible = false

func start_game(category_id: String) -> void:
	current_category = CategoryLoader.get_category(category_id)
	category_title_lbl.text = "🏀 " + current_category.get("title", "Over / Under").to_upper()
	prompt_lbl.text = current_category.get("prompt", "Which is MORE?").to_upper()

	raw_category_items = current_category.get("items", []).duplicate()

	GameManager.reset_current_game()
	_setup_lives_ui()
	_update_score_ui()

	_apply_filters_and_rebuild_game()

func _apply_filters_and_rebuild_game() -> void:
	# 1. Apply pre-game filters
	var filtered = _filter_items(raw_category_items, GameManager.current_filters)
	if filtered.size() < 2:
		filtered = raw_category_items.duplicate()

	# 2. Apply difficulty percentage (Easy = top 30%, Medium = top 60%, Hard = 100%)
	var diff = GameManager.current_difficulty.to_lower()
	if diff == "easy":
		var take_count = maxi(2, int(ceil(filtered.size() * 0.3)))
		items_pool = filtered.slice(0, take_count)
	elif diff == "medium":
		var take_count = maxi(2, int(ceil(filtered.size() * 0.6)))
		items_pool = filtered.slice(0, take_count)
	else:
		items_pool = filtered.duplicate()

	if items_pool.size() < 2:
		items_pool = raw_category_items.duplicate()

	items_pool.shuffle()
	recent_names.clear()
	upcoming_duels.clear()

	# Create initial duel
	var first_duel = _create_next_duel_set()

	# Maintain prefetch queue
	_maintain_duel_queue()

	# Prefetch images
	var initial_prefetch_items: Array = [first_duel.left, first_duel.right]
	for duel in upcoming_duels:
		initial_prefetch_items.append(duel.left)
		initial_prefetch_items.append(duel.right)
	WebImageLoader.prefetch_items(initial_prefetch_items)

	# Present duel
	current_left_item = first_duel.left
	current_right_item = first_duel.right
	var fmt = current_category.get("value_format", "{value}")
	duel_card.setup_duel(current_left_item, current_right_item, fmt)

	_update_active_filter_banner()

func _setup_lives_ui() -> void:
	if GameManager.is_free_play():
		for h in heart_nodes:
			h.visible = false
		free_play_icon.visible = true
		free_play_label.visible = true
	else:
		free_play_icon.visible = false
		free_play_label.visible = false
		var max_h = GameManager.get_max_lives()
		for i in range(heart_nodes.size()):
			if i < max_h:
				heart_nodes[i].visible = true
				heart_nodes[i].texture = BALL_FULL
				heart_nodes[i].modulate = Color(1, 1, 1, 1)
			else:
				heart_nodes[i].visible = false

func _update_lives_ui(lives_left: int) -> void:
	if GameManager.is_free_play():
		return

	var max_h = GameManager.get_max_lives()
	for i in range(max_h):
		if i < heart_nodes.size():
			if i < lives_left:
				heart_nodes[i].texture = BALL_FULL
				heart_nodes[i].modulate = Color(1, 1, 1, 1)
			else:
				heart_nodes[i].texture = BALL_EMPTY
				heart_nodes[i].modulate = Color(0.5, 0.5, 0.5, 0.6)

func _update_active_filter_banner() -> void:
	var parts: Array = []
	var diff_str = GameManager.current_difficulty.capitalize()
	var tier_name = "Rookie" if diff_str == "Easy" else ("All-Star" if diff_str == "Medium" else "Hall of Fame")
	parts.append("%s (%s)" % [tier_name, "Top 30%" if diff_str == "Easy" else ("Top 60%" if diff_str == "Medium" else "100%")])

	var filters = GameManager.current_filters
	if filters.get("position", "All") != "All":
		parts.append(filters["position"])
	if filters.get("decade", "All") != "All":
		parts.append(filters["decade"])
	if filters.get("status", "All") != "All":
		parts.append(filters["status"])
	if filters.get("team", "All") != "All":
		parts.append(filters["team"])
	if filters.get("conference", "All") != "All":
		parts.append(filters["conference"])

	active_filters_bar.visible = true
	active_filter_label.text = "🎯 Court Setup: " + " • ".join(parts) + " (%d contenders in pool)" % items_pool.size()

func _filter_items(raw_list: Array, filters: Dictionary) -> Array:
	var result: Array = []
	for item in raw_list:
		if _matches_filters(item, filters):
			result.append(item)
	return result

func _matches_filters(item: Dictionary, filters: Dictionary) -> bool:
	var pos_f = filters.get("position", "All")
	if pos_f != "All":
		var positions: Array = item.get("positions", [item.get("position", "")])
		if not positions.has(pos_f) and not pos_f in item.get("position", ""):
			return false

	var dec_f = filters.get("decade", "All")
	if dec_f != "All":
		var decades: Array = item.get("decades", [])
		if not decades.has(dec_f):
			return false

	var st_f = filters.get("status", "All")
	if st_f != "All":
		var status: String = item.get("status", "")
		if st_f == "Active Only" and status != "Active":
			return false
		elif st_f == "Legends Only" and status != "Retired":
			return false

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

	var conf_f = filters.get("conference", "All")
	if conf_f != "All":
		var item_conf = item.get("conference", "")
		if not conf_f.begins_with(item_conf) and not item_conf.begins_with(conf_f):
			return false

	return true

func _update_score_ui() -> void:
	streak_lbl.text = str(GameManager.current_score)
	if GameManager.is_free_play():
		best_lbl.text = "PRACTICE"
	else:
		best_lbl.text = "RECORD: %d" % GameManager.get_best_streak()

func _maintain_duel_queue() -> void:
	while upcoming_duels.size() < PREFETCH_SETS_AHEAD:
		var new_duel = _create_next_duel_set()
		upcoming_duels.append(new_duel)
		WebImageLoader.prefetch_items([new_duel.left, new_duel.right])

func _deal_new_duel() -> void:
	if upcoming_duels.is_empty():
		_maintain_duel_queue()

	var next_duel = upcoming_duels.pop_front()
	current_left_item = next_duel.left
	current_right_item = next_duel.right

	var fmt = current_category.get("value_format", "{value}")
	duel_card.setup_duel(current_left_item, current_right_item, fmt)

	_maintain_duel_queue()

func _create_next_duel_set() -> Dictionary:
	if items_pool.size() < 2:
		_apply_filters_and_rebuild_game()

	var left: Dictionary = _pick_item(recent_names)
	var right: Dictionary = _pick_item(recent_names + [left.get("name", "")])

	if abs(float(left.get("value", 0)) - float(right.get("value", 0))) < 0.00001 and items_pool.size() > 2:
		right = _pick_item(recent_names + [left.get("name", "")])

	recent_names.append(left.get("name", ""))
	recent_names.append(right.get("name", ""))
	while recent_names.size() > 10:
		recent_names.pop_front()

	return {"left": left, "right": right}

func _pick_item(exclude_names: Array) -> Dictionary:
	var candidates: Array = []
	for item in items_pool:
		if not exclude_names.has(item.get("name", "")):
			candidates.append(item)

	if candidates.is_empty():
		candidates = items_pool.duplicate()

	candidates.shuffle()
	return candidates[0]

func _on_manual_pick_left() -> void:
	if game_over_modal.visible:
		return
	duel_card.trigger_choice("left")

func _on_manual_pick_right() -> void:
	if game_over_modal.visible:
		return
	duel_card.trigger_choice("right")

func _unhandled_input(event: InputEvent) -> void:
	if duel_card.is_locked or game_over_modal.visible:
		return
	if event.is_action_pressed("ui_left"):
		_on_manual_pick_left()
	elif event.is_action_pressed("ui_right"):
		_on_manual_pick_right()

func _on_choice_made(side: String) -> void:
	var left_val = float(current_left_item.get("value", 0))
	var right_val = float(current_right_item.get("value", 0))

	var is_left_higher = left_val >= right_val
	var correct = (side == "left" and is_left_higher) or (side == "right" and not is_left_higher)

	if correct:
		var new_streak = GameManager.record_correct()
		var phrase = BASKETBALL_CORRECT_PHRASES[randi() % BASKETBALL_CORRECT_PHRASES.size()]
		_show_feedback(true, "%s STREAK: %d" % [phrase, new_streak])
		await get_tree().create_timer(1.0).timeout
		_hide_feedback()
		_deal_new_duel()
	else:
		var outcome = GameManager.record_wrong_guess()
		if outcome.get("game_over", false):
			_show_feedback(false, "FOUL OUT! 🛑 FINAL: %d" % GameManager.current_score)
			_update_lives_ui(0)
			# Game over triggered signal handles modal
		else:
			if GameManager.is_free_play():
				_show_feedback(false, "BRICK! 🧱 (Free Practice)")
			else:
				var left_count = outcome.get("lives_left", 0)
				var phrase = BASKETBALL_WRONG_PHRASES[randi() % BASKETBALL_WRONG_PHRASES.size()]
				_show_feedback(false, "%s (%d left)" % [phrase, left_count])
				_update_lives_ui(left_count)
			
			await get_tree().create_timer(1.0).timeout
			_hide_feedback()
			_deal_new_duel()

func _show_feedback(is_correct: bool, text: String) -> void:
	feedback_banner.visible = true
	feedback_label.text = text
	if is_correct:
		feedback_banner.self_modulate = Color(0.1, 0.85, 0.35, 0.98)
	else:
		feedback_banner.self_modulate = Color(0.95, 0.3, 0.15, 0.98)

	feedback_banner.scale = Vector2(0.8, 0.8)
	var tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(feedback_banner, "scale", Vector2.ONE, 0.22)

func _hide_feedback() -> void:
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tween.tween_property(feedback_banner, "scale", Vector2(0.8, 0.8), 0.15)
	await tween.finished
	feedback_banner.visible = false

func _on_score_changed(current: int, best: int) -> void:
	streak_lbl.text = str(current)
	if GameManager.is_free_play():
		best_lbl.text = "PRACTICE"
	else:
		best_lbl.text = "RECORD: %d" % best

	var tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(streak_lbl, "scale", Vector2(1.25, 1.25), 0.12)
	tween.tween_property(streak_lbl, "scale", Vector2.ONE, 0.12)

func _on_game_over(final_score: int, is_new_best: bool, cat_title: String, settings_str: String = "") -> void:
	await get_tree().create_timer(0.4).timeout
	_hide_feedback()
	game_over_modal.show_game_over(final_score, is_new_best, cat_title, settings_str)

func _on_retry_pressed() -> void:
	GameManager.reset_current_game()
	_setup_lives_ui()
	_update_score_ui()
	_apply_filters_and_rebuild_game()

func _on_back_pressed() -> void:
	AudioManager.play("click")
	return_to_menu_requested.emit()
