{
  "host_id": "HOST_ID",
  "host_api_version": "1.1",
  "aliases": ["ALIAS_1"],
  "support": {
    "level": "preview",
    "display_name": "DISPLAY_NAME",
    "evidence": null,
    "limitations": [
      "尚未完成目标客户端 E2E，支持等级为 preview",
      "遥测与插件自动更新未接入，需使用宿主原生插件管理手动更新"
    ]
  },
  "capabilities": {
    "command_surface": "native",
    "skill_discovery": "native",
    "session_start": "unsupported",
    "stop_hook": "unsupported",
    "failure_hook": "unsupported",
    "command_lifecycle": "emulated",
    "workflow_transition": "emulated",
    "subagents": "native",
    "unit_test_workflow": "emulated",
    "task_tracking": "emulated",
    "project_hooks": "unsupported",
    "session_events": "unsupported",
    "telemetry": "unsupported",
    "plugin_install": "native",
    "plugin_update": "unsupported",
    "session_end": "unsupported"
  },
  "adapters": {
    "command_projection": "resource:hosts/HOST_ID/command-projection.json",
    "detector": "python:update_hosts.generic:DETECTOR",
    "distribution": "resource:MANIFEST_PATH",
    "installer": "resource:hosts/HOST_ID/installer.md",
    "lifecycle": "resource:hosts/HOST_ID/lifecycle.md",
    "project_config": "resource:hosts/HOST_ID/project.json",
    "project_hooks": "resource:hosts/HOST_ID/project-hooks.json",
    "runtime": "resource:hosts/HOST_ID/runtime.md",
    "subagent_protocol": "resource:hosts/HOST_ID/subagent.md",
    "telemetry_protocol": "resource:hosts/shared/telemetry.md",
    "ut": "resource:hosts/HOST_ID/ut.md",
    "workflow_transition": "resource:hosts/HOST_ID/workflow-transition.md"
  }
}
