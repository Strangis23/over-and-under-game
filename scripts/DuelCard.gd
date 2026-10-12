extends Control

signal choice_made(chosen_side: String) # "left" or "right"

@export var swipe_threshold: float = 110.0
@export var max_rotation_deg: float = 14.0

var is_dragging: bool = false
var drag_start_pos: Vector2 = Vector2.ZERO
var current_offset: Vector2 = Vector2.ZERO
var is_locked: bool = false # locked during reveal animation

# References
@onready var card_panel: Control = $CardPanel
@onready var left_image: TextureRect = $CardPanel/HBox/LeftCard/ImageClip/LeftImage
@onready var left_name: Label = $CardPanel/HBox/LeftCard/InfoBox/Margin/Texts/LeftName
@onready var left_subtext: Label = $CardPanel/HBox/LeftCard/InfoBox/Margin/Texts/LeftSubtext
@onready var left_value_badge: PanelContainer = $CardPanel/HBox/LeftCard/ValueBadge
@onready var left_value_label: Label = $CardPanel/HBox/LeftCard/ValueBadge/LeftValue

@onready var right_image: TextureRect = $CardPanel/HBox/RightCard/ImageClip/RightImage
@onready var right_name: Label = $CardPanel/HBox/RightCard/InfoBox/Margin/Texts/RightName
@onready var right_subtext: Label = $CardPanel/HBox/RightCard/InfoBox/Margin/Texts/RightSubtext
@onready var right_value_badge: PanelContainer = $CardPanel/HBox/RightCard/ValueBadge
@onready var right_value_label: Label = $CardPanel/HBox/RightCard/ValueBadge/RightValue

@onready var pick_left_badge: Control = $CardPanel/PickLeftBadge
@onready var pick_right_badge: Control = $CardPanel/PickRightBadge
@onready var pick_left_text: Label = $CardPanel/PickLeftBadge/Label
@onready var pick_right_text: Label = $CardPanel/PickRightBadge/Label

@onready var left_highlight: Panel = $CardPanel/HBox/LeftCard/HighlightPanel
@onready var right_highlight: Panel = $CardPanel/HBox/RightCard/HighlightPanel

var initial_position: Vector2 = Vector2.ZERO
var item_left: Dictionary = {}
var item_right: Dictionary = {}
var value_format: String = "{value}"

func _ready() -> void:
	initial_position = card_panel.position
	pick_left_badge.modulate.a = 0.0
	pick_right_badge.modulate.a = 0.0
	left_value_badge.visible = false
	right_value_badge.visible = false
	left_highlight.visible = false
	right_highlight.visible = false

func setup_duel(left: Dictionary, right: Dictionary, format_str: String = "{value}") -> void:
	item_left = left
	item_right = right
	value_format = format_str
	is_locked = false
	is_dragging = false
	current_offset = Vector2.ZERO

	# Reset visual transforms
	card_panel.position = initial_position
	card_panel.rotation_degrees = 0.0
	card_panel.scale = Vector2.ONE
	card_panel.modulate = Color(1, 1, 1, 1)

	pick_left_badge.modulate.a = 0.0
	pick_right_badge.modulate.a = 0.0
	left_value_badge.visible = false
	right_value_badge.visible = false
	left_highlight.visible = false
	right_highlight.visible = false

	# Setup Left Candidate
	left_name.text = left.get("name", "Player 1")
	left_subtext.text = left.get("subtext", "")
	pick_left_text.text = "👈 " + left.get("name", "LEFT").to_upper()
	_load_image(left_image, left)

	# Setup Right Candidate
	right_name.text = right.get("name", "Player 2")
	right_subtext.text = right.get("subtext", "")
	pick_right_text.text = right.get("name", "RIGHT").to_upper() + " 👉"
	_load_image(right_image, right)

	# Entry animation: pop in
	card_panel.scale = Vector2(0.85, 0.85)
	card_panel.modulate.a = 0.0
	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(card_panel, "scale", Vector2.ONE, 0.35)
	tween.tween_property(card_panel, "modulate:a", 1.0, 0.25)

func _load_image(target_rect: TextureRect, item: Dictionary) -> void:
	WebImageLoader.load_image_for_item(item, target_rect)

var last_touch_local: Vector2 = Vector2.ZERO

func _gui_input(event: InputEvent) -> void:
	if is_locked:
		return

	var is_down = false
	var is_up = false
	var is_motion = false
	var curr_global = global_position + event.position

	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		is_down = event.pressed
		is_up = not event.pressed
		last_touch_local = event.position
	elif event is InputEventScreenTouch:
		is_down = event.pressed
		is_up = not event.pressed
		last_touch_local = event.position
	elif event is InputEventMouseMotion:
		is_motion = true
		last_touch_local = event.position
	elif event is InputEventScreenDrag:
		is_motion = true
		last_touch_local = event.position

	if is_down:
		is_dragging = true
		drag_start_pos = curr_global
		current_offset = Vector2.ZERO
	elif is_motion and is_dragging:
		var delta_x = curr_global.x - drag_start_pos.x
		var delta_y = (curr_global.y - drag_start_pos.y) * 0.25
		current_offset = Vector2(delta_x, delta_y)
		_update_card_drag_visuals()
	elif is_up and is_dragging:
		is_dragging = false
		_handle_drag_release()

func _update_card_drag_visuals() -> void:
	card_panel.position = initial_position + current_offset
	var rot_ratio = clamp(current_offset.x / 400.0, -1.0, 1.0)
	card_panel.rotation_degrees = rot_ratio * max_rotation_deg

	# Badges opacity & highlights
	var swipe_progress = clamp(abs(current_offset.x) / swipe_threshold, 0.0, 1.0)
	if current_offset.x < 0: # Dragging Left -> Pick Left Candidate
		pick_left_badge.modulate.a = swipe_progress
		pick_right_badge.modulate.a = 0.0
		left_highlight.visible = (swipe_progress > 0.4)
		right_highlight.visible = false
	else: # Dragging Right -> Pick Right Candidate
		pick_right_badge.modulate.a = swipe_progress
		pick_left_badge.modulate.a = 0.0
		right_highlight.visible = (swipe_progress > 0.4)
		left_highlight.visible = false

func _handle_drag_release() -> void:
	if current_offset.x <= -swipe_threshold:
		trigger_choice("left")
	elif current_offset.x >= swipe_threshold:
		trigger_choice("right")
	elif current_offset.length() < 35.0:
		# Direct tap on one of the contenders
		if last_touch_local.x < (size.x * 0.5):
			trigger_choice("left")
		else:
			trigger_choice("right")
	else:
		# Snap back
		var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tween.tween_property(card_panel, "position", initial_position, 0.3)
		tween.tween_property(card_panel, "rotation_degrees", 0.0, 0.3)
		tween.tween_property(pick_left_badge, "modulate:a", 0.0, 0.2)
		tween.tween_property(pick_right_badge, "modulate:a", 0.0, 0.2)
		left_highlight.visible = false
		right_highlight.visible = false

func trigger_choice(side: String) -> void:
	if is_locked:
		return
	is_locked = true
	AudioManager.play("swoosh")

	# Animate card fly-off slightly in chosen direction then snap to center for value reveal
	var fly_dir = -1.0 if side == "left" else 1.0
	var target_x = initial_position.x + (fly_dir * 160.0)
	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(card_panel, "position:x", target_x, 0.18)
	tween.tween_property(card_panel, "rotation_degrees", fly_dir * 8.0, 0.18)
	await tween.finished

	# Reveal values!
	_reveal_results(side)

func _reveal_results(chosen_side: String) -> void:
	var val_left: float = float(item_left.get("value", 0))
	var val_right: float = float(item_right.get("value", 0))

	# Format display
	if item_left.has("display_value") and not str(item_left["display_value"]).is_empty():
		left_value_label.text = str(item_left["display_value"])
	else:
		left_value_label.text = _format_value(val_left)

	if item_right.has("display_value") and not str(item_right["display_value"]).is_empty():
		right_value_label.text = str(item_right["display_value"])
	else:
		right_value_label.text = _format_value(val_right)

	left_value_badge.visible = true
	right_value_badge.visible = true
	left_value_badge.scale = Vector2(0.5, 0.5)
	right_value_badge.scale = Vector2(0.5, 0.5)

	# Determine winner
	var is_left_winner = val_left >= val_right
	var user_correct = (chosen_side == "left" and is_left_winner) or (chosen_side == "right" and not is_left_winner)

	# Pop badges
	var badge_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	badge_tween.tween_property(left_value_badge, "scale", Vector2.ONE, 0.3)
	badge_tween.tween_property(right_value_badge, "scale", Vector2.ONE, 0.3)
	badge_tween.tween_property(card_panel, "position", initial_position, 0.25)
	badge_tween.tween_property(card_panel, "rotation_degrees", 0.0, 0.25)

	# Visual indicator on winner / loser
	if is_left_winner:
		left_highlight.visible = true
		left_highlight.self_modulate = Color(0.2, 1.0, 0.4, 0.9)
		right_highlight.visible = true
		right_highlight.self_modulate = Color(1.0, 0.2, 0.2, 0.3)
	else:
		right_highlight.visible = true
		right_highlight.self_modulate = Color(0.2, 1.0, 0.4, 0.9)
		left_highlight.visible = true
		left_highlight.self_modulate = Color(1.0, 0.2, 0.2, 0.3)

	await get_tree().create_timer(0.45).timeout
	choice_made.emit(chosen_side)

func _format_value(val: float) -> String:
	if value_format.contains("{feet}") and value_format.contains("{inches}"):
		var total_inches: int = int(round(val))
		var feet: int = total_inches / 12
		var inches: int = total_inches % 12
		return value_format.replace("{feet}", str(feet)).replace("{inches}", str(inches))

	var s: String
	if val == floor(val):
		s = str(int(val))
	else:
		s = "%.2f" % val
	return value_format.replace("{value}", s)
