extends PanelContainer

signal selected(category_id: String)

@onready var title_label: Label = $Margin/VBox/Title
@onready var group_badge: Label = $Margin/VBox/TopRow/GroupBadge
@onready var icon_rect: TextureRect = $Margin/VBox/TopRow/CatIcon
@onready var prompt_label: Label = $Margin/VBox/Prompt
@onready var count_label: Label = $Margin/VBox/BottomRow/Count
@onready var best_label: Label = $Margin/VBox/BottomRow/BestStreak

var category_id: String = ""
var category_data: Dictionary = {}

# Touch / Drag gesture detection to allow smooth scrolling without accidental card launches
var touch_down: bool = false
var touch_start_global: Vector2 = Vector2.ZERO
var touch_start_time: int = 0
var touch_start_scroll_v: float = 0.0
var has_dragged: bool = false

# Generous thresholds for high-DPI mobile touchscreens
const DRAG_CANCEL_DISTANCE: float = 32.0   # Pixels moved before considering it a drag
const SCROLL_CANCEL_DISTANCE: float = 12.0 # ScrollContainer movement before canceling tap
const MAX_TAP_DURATION_MS: int = 750      # Max ms for a tap

# Dynamic styling
var card_style: StyleBoxFlat
var normal_border_color: Color = Color(0.25, 0.35, 0.5, 0.6)
var active_border_color: Color = Color(0.3, 0.8, 1.0, 0.9)

func _ready() -> void:
	# Enable pass so parent ScrollContainer receives scroll drag gestures
	mouse_filter = Control.MOUSE_FILTER_PASS
	pivot_offset = size / 2.0
	resized.connect(func(): pivot_offset = size / 2.0)

func setup(data: Dictionary) -> void:
	category_data = data
	category_id = data.get("id", "")
	title_label.text = data.get("title", "Category")
	prompt_label.text = data.get("prompt", "Who has more?")
	var items = data.get("items", [])

	if category_id == "random":
		title_label.text = "🎲 RANDOM SHUFFLE"
		count_label.text = "All 29 Categories"
		group_badge.visible = true
		group_badge.text = " 🎲 SHUFFLE "
	else:
		count_label.text = "%d Contenders" % items.size()
		var grp = data.get("group_label", "")
		if grp.is_empty():
			group_badge.visible = false
		else:
			group_badge.visible = true
			group_badge.text = " %s " % grp.to_upper()

	var best = GameManager.get_best_streak(category_id)
	best_label.text = "🏆 %d" % best

	# Custom theme colors based on group
	_apply_category_theme(data.get("group", ""), data.get("theme_color", ""))

func _apply_category_theme(group: String, hex_color: String) -> void:
	var base_col = Color(0.18, 0.65, 0.95)
	if not hex_color.is_empty():
		base_col = Color.from_string(hex_color, base_col)
	elif group == "physical":
		base_col = Color(0.2, 0.8, 0.95)
	elif group == "career":
		base_col = Color(0.95, 0.65, 0.2)
	elif group == "franchise":
		base_col = Color(0.65, 0.35, 0.95)

	normal_border_color = Color(base_col.r, base_col.g, base_col.b, 0.5)
	active_border_color = Color(base_col.r, base_col.g, base_col.b, 1.0)

	card_style = StyleBoxFlat.new()
	card_style.bg_color = Color(0.09, 0.12, 0.18, 0.95)
	card_style.border_color = normal_border_color
	card_style.set_border_width_all(2)
	card_style.set_corner_radius_all(18)
	card_style.shadow_color = Color(0, 0, 0, 0.35)
	card_style.shadow_size = 6
	add_theme_stylebox_override("panel", card_style)

func _get_parent_scroll() -> ScrollContainer:
	var p = get_parent()
	while p:
		if p is ScrollContainer:
			return p
		p = p.get_parent()
	return null

func _gui_input(event: InputEvent) -> void:
	var is_down: bool = false
	var is_up: bool = false
	var is_motion: bool = false
	var curr_pos: Vector2 = Vector2.ZERO

	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		is_down = event.pressed
		is_up = not event.pressed
		curr_pos = global_position + event.position
	elif event is InputEventScreenTouch:
		is_down = event.pressed
		is_up = not event.pressed
		curr_pos = global_position + event.position
	elif event is InputEventMouseMotion:
		is_motion = true
		curr_pos = global_position + event.position
	elif event is InputEventScreenDrag:
		is_motion = true
		curr_pos = global_position + event.position

	var scroll = _get_parent_scroll()

	if is_down:
		touch_down = true
		touch_start_global = curr_pos
		touch_start_time = Time.get_ticks_msec()
		has_dragged = false
		if scroll:
			touch_start_scroll_v = scroll.scroll_vertical
		_set_pressed_visuals(true)

	elif is_motion and touch_down:
		var dist = curr_pos.distance_to(touch_start_global)
		var scroll_diff = 0.0
		if scroll:
			scroll_diff = abs(scroll.scroll_vertical - touch_start_scroll_v)
		if dist > DRAG_CANCEL_DISTANCE or scroll_diff > SCROLL_CANCEL_DISTANCE:
			has_dragged = true
			_set_pressed_visuals(false)

	elif is_up and touch_down:
		touch_down = false
		_set_pressed_visuals(false)

		var elapsed = Time.get_ticks_msec() - touch_start_time
		var dist = curr_pos.distance_to(touch_start_global)
		var scroll_diff = 0.0
		if scroll:
			scroll_diff = abs(scroll.scroll_vertical - touch_start_scroll_v)

		# Tap is confirmed if finger didn't drag far, scroll didn't move far, and within tap time
		if not has_dragged and dist <= DRAG_CANCEL_DISTANCE and scroll_diff <= SCROLL_CANCEL_DISTANCE and elapsed <= MAX_TAP_DURATION_MS:
			_trigger_card_selection()

func _set_pressed_visuals(is_pressed_state: bool) -> void:
	if card_style:
		card_style.border_color = active_border_color if is_pressed_state else normal_border_color
		card_style.bg_color = Color(0.12, 0.16, 0.25, 0.98) if is_pressed_state else Color(0.09, 0.12, 0.18, 0.95)
	
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	var target_scale = Vector2(0.97, 0.97) if is_pressed_state else Vector2.ONE
	tween.tween_property(self, "scale", target_scale, 0.08)

func _trigger_card_selection() -> void:
	AudioManager.play("click")
	var tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "scale", Vector2(1.03, 1.03), 0.1)
	tween.tween_property(self, "scale", Vector2.ONE, 0.1)
	selected.emit(category_id)

