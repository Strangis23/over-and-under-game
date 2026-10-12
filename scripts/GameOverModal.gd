extends Control

signal retry_pressed
signal change_category_pressed

@onready var modal_panel: PanelContainer = $Center/Panel
@onready var score_label: Label = $Center/Panel/Margin/VBox/ScoreBox/FinalScore
@onready var best_label: Label = $Center/Panel/Margin/VBox/ScoreBox/BestScore
@onready var new_best_tag: Label = $Center/Panel/Margin/VBox/ScoreBox/NewBestTag
@onready var category_name: Label = $Center/Panel/Margin/VBox/CategoryTitle
@onready var settings_label: Label = $Center/Panel/Margin/VBox/SettingsTitle
@onready var retry_btn: Button = $Center/Panel/Margin/VBox/ButtonBox/RetryBtn
@onready var category_btn: Button = $Center/Panel/Margin/VBox/ButtonBox/CategoryBtn

func _ready() -> void:
	visible = false
	retry_btn.pressed.connect(_on_retry)
	category_btn.pressed.connect(_on_category)

func show_game_over(final_score: int, is_new_best: bool, cat_title: String, settings_str: String = "") -> void:
	visible = true
	category_name.text = cat_title
	if settings_label:
		settings_label.text = settings_str if not settings_str.is_empty() else "Standard Mode"
	
	score_label.text = str(final_score)
	if GameManager.is_free_play():
		best_label.text = "FREE PLAY (No high score kept)"
		new_best_tag.visible = false
	else:
		best_label.text = "BEST: %d" % GameManager.get_best_streak()
		new_best_tag.visible = is_new_best

	# Pop animation
	modal_panel.scale = Vector2(0.7, 0.7)
	modal_panel.modulate.a = 0.0
	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(modal_panel, "scale", Vector2.ONE, 0.3)
	tween.tween_property(modal_panel, "modulate:a", 1.0, 0.25)

func _on_retry() -> void:
	AudioManager.play("click")
	visible = false
	retry_pressed.emit()

func _on_category() -> void:
	AudioManager.play("click")
	visible = false
	change_category_pressed.emit()
