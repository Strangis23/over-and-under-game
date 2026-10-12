extends Node

var memory_cache: Dictionary = {} # item_name -> Texture2D
var active_downloads: Dictionary = {} # item_name -> bool
var listeners: Dictionary = {} # item_name -> Array[TextureRect]
var prefetch_queue: Array[Dictionary] = []
var queue_names: Dictionary = {} # item_name -> bool
var current_active_count: int = 0

const MAX_CONCURRENT: int = 4

const HEADERS = [
	"User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
	"Accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
]

const API_HEADERS = [
	"User-Agent: OverAndUnderTriviaGame/2.0 (contact: dev@overundergame.org)"
]

func prefetch_items(items: Array) -> void:
	for it in items:
		if it is Dictionary:
			prefetch_item(it)

func prefetch_item(item: Dictionary) -> void:
	var item_name: String = item.get("name", "")
	if item_name.is_empty():
		return
	if memory_cache.has(item_name) or active_downloads.has(item_name) or queue_names.has(item_name):
		return
	
	queue_names[item_name] = true
	prefetch_queue.append(item)
	_pump_queue()

func load_image_for_item(item: Dictionary, target_rect: TextureRect) -> void:
	var item_name: String = item.get("name", "")
	if item_name.is_empty():
		target_rect.texture = null
		return

	target_rect.set_meta("loading_item_name", item_name)

	# 1. In-memory cache hit: instant zero-delay display
	if memory_cache.has(item_name):
		target_rect.texture = memory_cache[item_name]
		return

	# 2. Local fallback if exists while waiting for web image
	var local_path: String = item.get("image", "")
	if not local_path.is_empty() and ResourceLoader.exists(local_path):
		var local_tex = load(local_path)
		if local_tex:
			target_rect.texture = local_tex
		else:
			target_rect.texture = null
	else:
		target_rect.texture = null

	# 3. Register target_rect as listener
	if not listeners.has(item_name):
		listeners[item_name] = []
	if not listeners[item_name].has(target_rect):
		listeners[item_name].append(target_rect)

	# 4. If already actively downloading, the listener will be served upon completion
	if active_downloads.has(item_name):
		return

	# 5. Prioritize this item to the front of prefetch queue
	if queue_names.has(item_name):
		for i in range(prefetch_queue.size()):
			if prefetch_queue[i].get("name", "") == item_name:
				var found = prefetch_queue[i]
				prefetch_queue.remove_at(i)
				prefetch_queue.push_front(found)
				break
	else:
		queue_names[item_name] = true
		prefetch_queue.push_front(item)

	_pump_queue()

func _pump_queue() -> void:
	while current_active_count < MAX_CONCURRENT and not prefetch_queue.is_empty():
		var item: Dictionary = prefetch_queue.pop_front()
		var item_name: String = item.get("name", "")
		queue_names.erase(item_name)

		if memory_cache.has(item_name) or active_downloads.has(item_name):
			continue

		active_downloads[item_name] = true
		current_active_count += 1
		_start_fetch_pipeline(item)

func _start_fetch_pipeline(item: Dictionary) -> void:
	var item_name: String = item.get("name", "")
	var direct_url: String = item.get("image_url", "")

	if not direct_url.is_empty() and direct_url.begins_with("http"):
		_request_direct_url(direct_url, item_name, func(success: bool):
			if not success:
				_search_wikipedia_image(item_name, func(wiki_success: bool):
					_finish_item_task(item_name, wiki_success)
				)
			else:
				_finish_item_task(item_name, true)
		)
	else:
		_search_wikipedia_image(item_name, func(wiki_success: bool):
			_finish_item_task(item_name, wiki_success)
		)

func _finish_item_task(item_name: String, success: bool) -> void:
	active_downloads.erase(item_name)
	current_active_count = max(0, current_active_count - 1)

	if listeners.has(item_name):
		var target_list: Array = listeners[item_name]
		listeners.erase(item_name)
		if success and memory_cache.has(item_name):
			var tex: Texture2D = memory_cache[item_name]
			for rect in target_list:
				_apply_texture_if_still_matching(rect, item_name, tex)

	_pump_queue()

func _request_direct_url(url: String, item_name: String, on_done: Callable) -> void:
	var http = HTTPRequest.new()
	http.use_threads = true
	http.timeout = 8.0
	add_child(http)

	http.request_completed.connect(func(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if result == HTTPRequest.RESULT_SUCCESS and response_code == 200 and body.size() > 500:
			var tex = _buffer_to_texture(body)
			if tex:
				memory_cache[item_name] = tex
				on_done.call(true)
				return
		on_done.call(false)
	)

	var err = http.request(url, HEADERS)
	if err != OK:
		http.queue_free()
		on_done.call(false)

func _search_wikipedia_image(item_name: String, on_done: Callable) -> void:
	var http = HTTPRequest.new()
	http.use_threads = true
	http.timeout = 8.0
	add_child(http)

	var encoded = item_name.uri_encode()
	var api_url = "https://en.wikipedia.org/w/api.php?action=query&titles=%s&prop=pageimages&format=json&pithumbsize=600" % encoded

	http.request_completed.connect(func(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if result == HTTPRequest.RESULT_SUCCESS and response_code == 200 and body.size() > 10:
			var json = JSON.new()
			if json.parse(body.get_string_from_utf8()) == OK:
				var data = json.get_data()
				var pages = data.get("query", {}).get("pages", {})
				for pid in pages:
					var p = pages[pid]
					if p.has("thumbnail") and p["thumbnail"].has("source"):
						var img_src: String = p["thumbnail"]["source"]
						_download_wiki_media(img_src, item_name, on_done)
						return

		if "(" in item_name:
			var clean_name = item_name.split("(")[0].strip_edges()
			if clean_name != item_name:
				_search_wikipedia_image(clean_name, on_done)
				return

		on_done.call(false)
	)

	var err = http.request(api_url, API_HEADERS)
	if err != OK:
		http.queue_free()
		on_done.call(false)

func _download_wiki_media(img_url: String, item_name: String, on_done: Callable) -> void:
	var http = HTTPRequest.new()
	http.use_threads = true
	http.timeout = 8.0
	add_child(http)

	http.request_completed.connect(func(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if result == HTTPRequest.RESULT_SUCCESS and response_code == 200 and body.size() > 500:
			var tex = _buffer_to_texture(body)
			if tex:
				memory_cache[item_name] = tex
				on_done.call(true)
				return
		on_done.call(false)
	)

	var err = http.request(img_url, HEADERS)
	if err != OK:
		http.queue_free()
		on_done.call(false)

func _apply_texture_if_still_matching(target_rect: TextureRect, item_name: String, texture: Texture2D) -> void:
	if is_instance_valid(target_rect) and target_rect.get_meta("loading_item_name", "") == item_name:
		target_rect.texture = texture
		target_rect.modulate.a = 0.5
		var tween = target_rect.create_tween()
		tween.tween_property(target_rect, "modulate:a", 1.0, 0.25)

func _buffer_to_texture(buffer: PackedByteArray) -> Texture2D:
	if buffer.size() < 16:
		return null

	var img = Image.new()
	var err: Error = FAILED

	if buffer[0] == 0xFF and buffer[1] == 0xD8:
		err = img.load_jpg_from_buffer(buffer)
	elif buffer[0] == 0x89 and buffer[1] == 0x50 and buffer[2] == 0x4E and buffer[3] == 0x47:
		err = img.load_png_from_buffer(buffer)
	elif buffer[0] == 0x52 and buffer[1] == 0x49 and buffer[2] == 0x46 and buffer[3] == 0x46:
		err = img.load_webp_from_buffer(buffer)
	elif buffer[0] == 0x3C and img.has_method("load_svg_from_buffer"):
		err = img.load_svg_from_buffer(buffer)

	if err == OK:
		return ImageTexture.create_from_image(img)
	return null
