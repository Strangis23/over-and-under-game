extends Node

signal score_changed(current_score: int, best_score: int)
signal lives_changed(remaining_lives: int, max_lives: Variant)
signal streak_celebrated(streak: int)
signal game_over_triggered(final_score: int, is_new_best: bool, category_title: String, settings_summary: String)

var current_category_id: String = "nba_ppg"
var current_score: int = 0
var best_streaks: Dictionary = {} # cat_id -> int

# Game settings
var current_difficulty: String = "easy" # "easy", "medium", "hard"
var current_lives_mode: Variant = 3     # 1, 3, 5, or "free_play"
var current_filters: Dictionary = {}
var lives_remaining: int = 3

# Overall stats
var total_guesses: int = 0
var total_correct: int = 0
var total_games_played: int = 0
var high_scores: Array = [] # Array of Dictionary entries

const STATS_PATH = "user://game_stats.cfg"
const HIGH_SCORES_PATH = "user://high_scores.json"

func _ready() -> void:
	load_stats()
	load_high_scores()

func set_game_setup(cat_id: String, difficulty: String, lives_mode: Variant, filters: Dictionary) -> void:
	current_category_id = cat_id
	current_difficulty = difficulty
	current_lives_mode = lives_mode
	current_filters = filters.duplicate()
	current_score = 0
	
	if str(current_lives_mode) == "free_play":
		lives_remaining = 999
	else:
		lives_remaining = int(current_lives_mode)

func is_free_play() -> bool:
	return str(current_lives_mode) == "free_play"

func get_max_lives() -> int:
	return 0 if is_free_play() else int(current_lives_mode)

func get_current_category() -> Dictionary:
	return CategoryLoader.get_category(current_category_id)

func get_best_streak(cat_id: String = "") -> int:
	if cat_id.is_empty():
		cat_id = current_category_id
	return best_streaks.get(cat_id, 0)

func record_correct() -> int:
	current_score += 1
	total_guesses += 1
	total_correct += 1

	var best = get_best_streak()
	var is_new_record = false
	if str(current_lives_mode) != "free_play" and current_score > best:
		best_streaks[current_category_id] = current_score
		best = current_score
		is_new_record = true

	score_changed.emit(current_score, best)
	save_stats()

	# Streak celebration milestones
	if current_score > 0 and current_score % 5 == 0:
		streak_celebrated.emit(current_score)
		AudioManager.play("streak")
	else:
		AudioManager.play("correct", 1.0 + min(current_score * 0.05, 0.5))

	return current_score

func record_wrong_guess() -> Dictionary:
	# Returns {"game_over": bool, "lives_left": int}
	total_guesses += 1
	AudioManager.play("wrong")

	if is_free_play():
		# In free play, streak resets to 0 but no game over
		current_score = 0
		score_changed.emit(0, get_best_streak())
		return {"game_over": false, "lives_left": 999}

	lives_remaining -= 1
	lives_changed.emit(lives_remaining, current_lives_mode)

	if lives_remaining <= 0:
		lives_remaining = 0
		var final_score = current_score
		var best = get_best_streak()
		var is_new_record = (final_score > best and final_score > 0)

		var cat_data = get_current_category()
		var title = cat_data.get("title", "Over / Under")

		var settings_str = "%s • %s" % [
			current_difficulty.capitalize(),
			"1 Life" if str(current_lives_mode) == "1" else ("%s Lives" % str(current_lives_mode))
		]

		if final_score > 0:
			_record_high_score(current_category_id, title, final_score, current_difficulty, current_lives_mode, current_filters)

		total_games_played += 1
		save_stats()

		game_over_triggered.emit(final_score, is_new_record, title, settings_str)
		current_score = 0
		score_changed.emit(0, get_best_streak())
		return {"game_over": true, "lives_left": 0}
	else:
		# Lost a life but still playing
		return {"game_over": false, "lives_left": lives_remaining}

func reset_current_game() -> void:
	current_score = 0
	if is_free_play():
		lives_remaining = 999
	else:
		lives_remaining = int(current_lives_mode)
	score_changed.emit(0, get_best_streak())
	lives_changed.emit(lives_remaining, current_lives_mode)

func _record_high_score(cat_id: String, cat_title: String, score: int, difficulty: String, lives_mode: Variant, filters: Dictionary) -> void:
	var date_dict = Time.get_date_dict_from_system()
	var date_str = "%04d-%02d-%02d" % [date_dict["year"], date_dict["month"], date_dict["day"]]

	var lives_label = "1 Life" if str(lives_mode) == "1" else ("%s Lives" % str(lives_mode))
	var filter_summary = _summarize_filters(filters)

	var entry = {
		"id": "%d_%d" % [Time.get_unix_time_from_system(), randi() % 1000],
		"category_id": cat_id,
		"category_title": cat_title,
		"score": score,
		"difficulty": difficulty.capitalize(),
		"lives": lives_label,
		"lives_raw": lives_mode,
		"filters": filter_summary,
		"date": date_str,
		"timestamp": Time.get_unix_time_from_system()
	}

	high_scores.append(entry)
	# Sort high scores descending by score
	high_scores.sort_custom(func(a, b):
		return a.get("score", 0) > b.get("score", 0)
	)

	# Cap at top 100 records
	if high_scores.size() > 100:
		high_scores = high_scores.slice(0, 100)

	save_high_scores()

func _summarize_filters(filters: Dictionary) -> String:
	var parts: Array = []
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

	return " • ".join(parts) if not parts.is_empty() else "All Contenders"

func get_filtered_high_scores(cat_filter: String = "All", diff_filter: String = "All", lives_filter: String = "All") -> Array:
	var result: Array = []
	for entry in high_scores:
		if cat_filter != "All" and entry.get("category_id", "") != cat_filter and entry.get("category_title", "") != cat_filter:
			continue
		if diff_filter != "All" and entry.get("difficulty", "").to_lower() != diff_filter.to_lower():
			continue
		if lives_filter != "All":
			var lives_str = str(entry.get("lives", "")).to_lower()
			if not lives_filter.to_lower() in lives_str:
				continue
		result.append(entry)
	return result

func clear_high_scores() -> void:
	high_scores.clear()
	best_streaks.clear()
	save_high_scores()
	save_stats()

func save_high_scores() -> void:
	var file = FileAccess.open(HIGH_SCORES_PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(high_scores, "\t"))
		file.close()

func load_high_scores() -> void:
	high_scores.clear()
	if not FileAccess.file_exists(HIGH_SCORES_PATH):
		return
	var file = FileAccess.open(HIGH_SCORES_PATH, FileAccess.READ)
	if not file:
		return
	var text = file.get_as_text()
	var json = JSON.new()
	if json.parse(text) == OK:
		var data = json.get_data()
		if typeof(data) == TYPE_ARRAY:
			high_scores = data
			high_scores.sort_custom(func(a, b):
				return a.get("score", 0) > b.get("score", 0)
			)

func save_stats() -> void:
	var cfg = ConfigFile.new()
	for cat_id in best_streaks:
		cfg.set_value("best_streaks", cat_id, best_streaks[cat_id])
	cfg.set_value("totals", "total_guesses", total_guesses)
	cfg.set_value("totals", "total_correct", total_correct)
	cfg.set_value("totals", "total_games_played", total_games_played)
	cfg.save(STATS_PATH)

func load_stats() -> void:
	var cfg = ConfigFile.new()
	var err = cfg.load(STATS_PATH)
	if err == OK:
		if cfg.has_section("best_streaks"):
			for key in cfg.get_section_keys("best_streaks"):
				best_streaks[key] = cfg.get_value("best_streaks", key, 0)
		total_guesses = cfg.get_value("totals", "total_guesses", 0)
		total_correct = cfg.get_value("totals", "total_correct", 0)
		total_games_played = cfg.get_value("totals", "total_games_played", 0)
