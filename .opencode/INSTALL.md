# Installing AgenticAISkills for OpenCode

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## Installation

Add this repository to the `plugin` array in your `opencode.json`:

```json
{
  "plugin": ["agentic-ai-skills@git+https://github.com/AgenticAIPlan/AgenticAISkills.git"]
}
```

Restart OpenCode after updating the config.

## What this plugin does

- registers this repository's `skills/` directory into OpenCode skill discovery
- lets OpenCode load the business skills in this repository without manual symlinks

## Verify

After restarting OpenCode, use its native skill listing flow to confirm that the skills from this repository are available.

## Updating

The plugin updates when OpenCode refreshes the configured git plugin source.

To pin a version, use a git ref:

```json
{
  "plugin": ["agentic-ai-skills@git+https://github.com/AgenticAIPlan/AgenticAISkills.git#main"]
}
```
