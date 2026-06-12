(dual-agent) E:\AI Agent\ai-agent-projects-main\Telephone_Agent\AudioAgentSecurity-BB64>python generate_distance_baseline.py --model_name gemini-3-pro-preview
05/26/2026 22:42:12 - INFO - __main__ - Loading model: gemini-3-pro-preview
05/26/2026 22:42:12 - INFO - src.model_src.universal_model - Loading model (OpenAI-compatible): gemini-3-pro-preview
05/26/2026 22:42:13 - INFO - src.model_src.universal_model - Client loaded for deployment: gemini-3-pro-preview
05/26/2026 22:42:13 - INFO - src.model - Loaded model: gemini-3-pro-preview
05/26/2026 22:42:13 - INFO - src.model - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
05/26/2026 22:42:13 - INFO - __main__ - Generating baseline for: '把卧室的灯调的亮一些'
05/26/2026 22:42:18 - INFO - httpx - HTTP Request: POST https://api.rcouyi.com/v1/chat/completions "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "E:\AI Agent\ai-agent-projects-main\Telephone_Agent\AudioAgentSecurity-BB64\generate_distance_baseline.py", line 100, in <module>
    fire.Fire(generate_distance_baseline)
  File "D:\anaconda\envs\dual-agent\Lib\site-packages\fire\core.py", line 135, in Fire
    component_trace = _Fire(component, args, parsed_flag_args, context, name)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\anaconda\envs\dual-agent\Lib\site-packages\fire\core.py", line 468, in _Fire
    component, remaining_args = _CallAndUpdateTrace(
                                ^^^^^^^^^^^^^^^^^^^^
  File "D:\anaconda\envs\dual-agent\Lib\site-packages\fire\core.py", line 684, in _CallAndUpdateTrace
    component = fn(*varargs, **kwargs)
                ^^^^^^^^^^^^^^^^^^^^^^
  File "E:\AI Agent\ai-agent-projects-main\Telephone_Agent\AudioAgentSecurity-BB64\generate_distance_baseline.py", line 55, in generate_distance_baseline
    response = model.client.chat.completions.create(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\anaconda\envs\dual-agent\Lib\site-packages\openai\_utils\_utils.py", line 286, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "D:\anaconda\envs\dual-agent\Lib\site-packages\openai\resources\chat\completions\completions.py", line 1211, in create
    return self._post(
           ^^^^^^^^^^^
  File "D:\anaconda\envs\dual-agent\Lib\site-packages\openai\_base_client.py", line 1297, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\anaconda\envs\dual-agent\Lib\site-packages\openai\_base_client.py", line 1070, in request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'message': 'Publisher Model `projects/goclases/locations/global/publishers/google/models/gemini-3-pro-preview` was not found or your project does not have access to it. Please ensure you are using a valid model version. For more information, see: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions  (request id: 2026052622423777681932651911180)', 'type': 'v_api_biz_error', 'param': '', 'code': 404}}