extends Node

var sounds: Dictionary = {}
var is_muted: bool = false
var players: Array[AudioStreamPlayer] = []
const POOL_SIZE = 8

func _ready() -> void:
	# Load sound files
	_load_sound("click", "res://assets/audio/click.wav")
	_load_sound("swoosh", "res://assets/audio/swoosh.wav")
	_load_sound("correct", "res://assets/audio/correct.wav")
	_load_sound("wrong", "res://assets/audio/wrong.wav")
	_load_sound("streak", "res://assets/audio/streak.wav")

	# Create player pool
	for i in range(POOL_SIZE):
		var p = AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		players.append(p)

func _load_sound(sound_name: String, path: String) -> void:
	if ResourceLoader.exists(path):
		var stream = load(path)
		if stream:
			sounds[sound_name] = stream

func play(sound_name: String, pitch_scale: float = 1.0, volume_db: float = 0.0) -> void:
	if is_muted:
		return
	if not sounds.has(sound_name):
		return

	# Find available player
	for p in players:
		if not p.playing:
			p.stream = sounds[sound_name]
			p.pitch_scale = pitch_scale
			p.volume_db = volume_db
			p.play()
			return

	# Fallback: steal first player
	var fallback_player = players[0]
	fallback_player.stream = sounds[sound_name]
	fallback_player.pitch_scale = pitch_scale
	fallback_player.volume_db = volume_db
	fallback_player.play()

func toggle_mute() -> bool:
	is_muted = not is_muted
	return is_muted
