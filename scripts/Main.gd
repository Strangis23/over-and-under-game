extends Control

@onready var category_select = $CategorySelect
@onready var game_screen = $Game

func _ready() -> void:
	category_select.visible = true
	game_screen.visible = false

	category_select.start_game_requested.connect(_on_start_game)
	game_screen.return_to_menu_requested.connect(_on_return_to_menu)

func _on_start_game(category_id: String) -> void:
	category_select.visible = false
	game_screen.visible = true
	game_screen.start_game(category_id)

func _on_return_to_menu() -> void:
	game_screen.visible = false
	category_select.visible = true
	category_select.refresh_categories()
