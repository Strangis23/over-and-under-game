extends Node

var categories: Dictionary = {}
var category_order: Array = []

func _ready() -> void:
	load_all_categories()

func load_all_categories() -> void:
	categories.clear()
	category_order.clear()

	# 1. Built-in categories
	_scan_directory("res://data/categories/")

	# 2. User custom categories
	var user_cat_dir := "user://custom_categories/"
	if not DirAccess.dir_exists_absolute(user_cat_dir):
		DirAccess.make_dir_recursive_absolute(user_cat_dir)
	_scan_directory(user_cat_dir)

	# Sort in curated order
	const PREFERRED_ORDER = [
		"nba_height",
		"nba_weight",
		"nba_wingspan",
		"nba_vertical_leap",
		"nba_bench_press",
		"nba_ppg",
		"nba_seasons_played",
		"nba_draft_pick",
		"nba_franchise_wins",
		"nba_franchise_win_pct",
		"nba_arena_capacity",
		"nba_franchise_founded"
	]
	category_order.sort_custom(func(a, b):
		var idx_a = PREFERRED_ORDER.find(a)
		var idx_b = PREFERRED_ORDER.find(b)
		if idx_a != -1 and idx_b != -1:
			return idx_a < idx_b
		elif idx_a != -1:
			return true
		elif idx_b != -1:
			return false
		return a < b
	)

	print("[CategoryLoader] Loaded %d categories: %s" % [categories.size(), str(category_order)])

func _scan_directory(dir_path: String) -> void:
	var dir = DirAccess.open(dir_path)
	if not dir:
		return
	dir.list_dir_begin()
	var file_name = dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".json"):
			var full_path = dir_path.path_join(file_name)
			_load_category_file(full_path)
		file_name = dir.get_next()
	dir.list_dir_end()

func _load_category_file(file_path: String) -> void:
	var file = FileAccess.open(file_path, FileAccess.READ)
	if not file:
		push_warning("Could not open category file: " + file_path)
		return
	var text = file.get_as_text()
	var json = JSON.new()
	var err = json.parse(text)
	if err != OK:
		push_error("Error parsing JSON %s: %s at line %d" % [file_path, json.get_error_message(), json.get_error_line()])
		return

	var data = json.get_data()
	if typeof(data) != TYPE_DICTIONARY:
		push_error("Invalid category JSON format in: " + file_path)
		return

	if not data.has("id") or not data.has("items") or data["items"].size() < 2:
		push_warning("Skipping invalid/empty category in: " + file_path)
		return

	var cat_id: String = data["id"]
	data["source_path"] = file_path
	categories[cat_id] = data
	if not category_order.has(cat_id):
		category_order.append(cat_id)

func get_all_categories() -> Array:
	var list := []
	for id in category_order:
		if categories.has(id):
			list.append(categories[id])
	return list

func get_category(id: String) -> Dictionary:
	return categories.get(id, {})

func save_custom_category(cat_dict: Dictionary) -> bool:
	if not cat_dict.has("id") or not cat_dict.has("title") or not cat_dict.has("items"):
		return false
	var cat_id = cat_dict["id"]
	var file_path = "user://custom_categories/%s.json" % cat_id
	var file = FileAccess.open(file_path, FileAccess.WRITE)
	if not file:
		return false
	file.store_string(JSON.stringify(cat_dict, "\t"))
	file.close()
	_load_category_file(file_path)
	return true
