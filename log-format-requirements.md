# CrashLens Log Format Requirements Report

## Overview
CrashLens is designed to analyze **Langfuse-style JSONL logs** for GPT API usage patterns and token waste detection. This report details the expected log formats, required fields, optional fields, and provides examples of supported log structures.

**Supported Input Format:** JSONL (JSON Lines) - One JSON object per line
**Primary Log Style:** Langfuse-compatible generation logs
**File Extension:** `.jsonl`

---

## Core Log Format: Langfuse Generation Logs

### Required JSON Structure
Each line in the JSONL file must be a valid JSON object representing a single API generation call.

### Primary Format (Recommended)

```json
{
  "traceId": "string",
  "type": "generation",
  "startTime": "ISO8601 timestamp",
  "endTime": "ISO8601 timestamp (optional)",
  "level": "info|error|warning",
  "input": {
    "model": "model_name",
    "prompt": "the input prompt text"
  },
  "usage": {
    "prompt_tokens": number,
    "completion_tokens": number,
    "total_tokens": number (optional)
  },
  "metadata": {
    "fallback_attempted": boolean,
    "fallback_reason": "string (optional)",
    "source": "string (optional)"
  },
  "name": "string (optional)",
  "cost": number (optional)
}
```

---

## Required Fields

### Core Identification
- **`traceId`** *(string, required)*
  - Unique identifier for grouping related API calls
  - Used to detect retry loops and fallback patterns
  - Example: `"trace_001"`, `"retry_loop_01"`

- **`type`** *(string, required)*
  - Must be `"generation"` for CrashLens to process the record
  - Only generation-type records are analyzed
  - Other types (e.g., "span", "event") are ignored

### Timing Information
- **`startTime`** *(string, required)*
  - ISO8601 formatted timestamp
  - Used for time-window analysis in retry and fallback detection
  - Example: `"2024-06-01T10:00:00Z"`

### Input Data
- **`input.model`** *(string, required)*
  - The AI model used for the generation
  - Critical for cost calculation and overkill detection
  - Examples: `"gpt-4"`, `"gpt-3.5-turbo"`, `"claude-3-opus-20240229"`

- **`input.prompt`** *(string, required)*
  - The input prompt sent to the model
  - Used for retry detection (exact matching) and overkill analysis (length)
  - Can be any length, but very long prompts may be truncated in reports

### Usage Metrics
- **`usage.prompt_tokens`** *(number, required)*
  - Number of tokens in the input prompt
  - Essential for cost calculation and overkill detection
  - Used to identify short prompts using expensive models

- **`usage.completion_tokens`** *(number, required)*
  - Number of tokens in the model's response
  - Required for accurate cost calculation
  - Used in total waste cost estimation

---

## Optional Fields

### Extended Timing
- **`endTime`** *(string, optional)*
  - ISO8601 formatted timestamp for call completion
  - Used for duration analysis when available
  - Example: `"2024-06-01T10:00:05Z"`

### Log Level
- **`level`** *(string, optional)*
  - Log severity level: `"info"`, `"error"`, `"warning"`
  - Used for error pattern analysis
  - Defaults to `"info"` if not provided

### Metadata Enhancement
- **`metadata.fallback_attempted`** *(boolean, optional)*
  - Indicates if this call was part of a fallback sequence
  - Critical for fallback pattern detection
  - Example: `true` for fallback calls, `false` for primary calls

- **`metadata.fallback_reason`** *(string, optional)*
  - Reason for fallback (e.g., "timeout", "rate_limit", "error")
  - Provides context for fallback analysis
  - Example: `"timeout"`, `"rate_limit_exceeded"`

- **`metadata.source`** *(string, optional)*
  - Source system or API endpoint
  - Used for categorization and filtering
  - Example: `"api"`, `"batch_job"`, `"web_interface"`

### Additional Context
- **`name`** *(string, optional)*
  - Human-readable name for the operation
  - Used in reports for better identification
  - Example: `"translation"`, `"summary"`, `"chat_response"`

- **`usage.total_tokens`** *(number, optional)*
  - Sum of prompt_tokens + completion_tokens
  - If provided, used for validation
  - Calculated automatically if missing

- **`cost`** *(number, optional)*
  - Pre-calculated cost for the API call
  - If provided, used instead of calculated cost
  - Useful for custom pricing models

---

## Supported Model Formats

### GPT Models
- `gpt-4` - High-cost flagship model
- `gpt-4-turbo` - Optimized GPT-4 variant
- `gpt-3.5-turbo` - Cost-effective model
- `gpt-3.5-turbo-16k` - Extended context version

### Claude Models
- `claude-3-opus-20240229` - Most capable, highest cost
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-haiku-20240307` - Fast and cost-effective

### Other Supported Models
- `gemini-pro` - Google's flagship model
- `gemini-pro-vision` - Multimodal variant
- Custom model names (with pricing configuration)

---

## Detection-Specific Requirements

### Retry Loop Detection
**Required Fields:**
- `traceId` - Groups retries together
- `input.prompt` - Exact matching for retry identification
- `input.model` - Must be same model for retry detection
- `startTime` - Time window analysis
- `usage.prompt_tokens` & `usage.completion_tokens` - Cost calculation

### Overkill Model Detection
**Required Fields:**
- `input.model` - Identifies expensive models
- `input.prompt` - Length analysis (tokens and characters)
- `usage.prompt_tokens` - Short prompt detection
- `usage.completion_tokens` - Cost calculation

### Fallback Pattern Detection
**Required Fields:**
- `traceId` - Groups related calls
- `input.model` - Model tier analysis
- `input.prompt` - Similar prompt identification
- `startTime` - Sequence timing analysis
- `metadata.fallback_attempted` - Fallback identification

### Fallback Storm Detection  
**Required Fields:**
- `traceId` - Storm identification within trace
- `startTime` - Time window analysis
- `input.model` - Fallback chain analysis

---

## Example Log Formats

### 1. Basic Generation Log
```json
{
  "traceId": "simple_001",
  "type": "generation",
  "startTime": "2024-06-01T10:00:00Z",
  "input": {
    "model": "gpt-3.5-turbo",
    "prompt": "What is 2+2?"
  },
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 3
  }
}
```

### 2. Retry Loop Pattern
```json
{"traceId": "retry_001", "type": "generation", "startTime": "2024-06-01T10:00:00Z", "input": {"model": "gpt-3.5-turbo", "prompt": "What is the weather?"}, "usage": {"prompt_tokens": 6, "completion_tokens": 0}}
{"traceId": "retry_001", "type": "generation", "startTime": "2024-06-01T10:00:02Z", "input": {"model": "gpt-3.5-turbo", "prompt": "What is the weather?"}, "usage": {"prompt_tokens": 6, "completion_tokens": 15}}
{"traceId": "retry_001", "type": "generation", "startTime": "2024-06-01T10:00:04Z", "input": {"model": "gpt-3.5-turbo", "prompt": "What is the weather?"}, "usage": {"prompt_tokens": 6, "completion_tokens": 15}}
```

### 3. Fallback Pattern
```json
{"traceId": "fallback_001", "type": "generation", "startTime": "2024-06-01T11:00:00Z", "level": "error", "input": {"model": "gpt-4", "prompt": "Translate hello"}, "usage": {"prompt_tokens": 3, "completion_tokens": 0}, "metadata": {"fallback_attempted": true, "fallback_reason": "timeout"}}
{"traceId": "fallback_001", "type": "generation", "startTime": "2024-06-01T11:00:02Z", "level": "info", "input": {"model": "gpt-3.5-turbo", "prompt": "Translate hello"}, "usage": {"prompt_tokens": 3, "completion_tokens": 2}, "metadata": {"fallback_attempted": false}}
```

### 4. Overkill Model Usage
```json
{
  "traceId": "overkill_001",
  "type": "generation",
  "startTime": "2024-06-01T12:00:00Z",
  "input": {
    "model": "gpt-4",
    "prompt": "Hi"
  },
  "usage": {
    "prompt_tokens": 2,
    "completion_tokens": 1
  },
  "cost": 0.000300
}
```

### 5. Enhanced Metadata
```json
{
  "traceId": "enhanced_001",
  "type": "generation",
  "startTime": "2024-06-01T13:00:00Z",
  "endTime": "2024-06-01T13:00:05Z",
  "level": "info",
  "input": {
    "model": "claude-3-opus-20240229",
    "prompt": "Write a comprehensive analysis of market trends"
  },
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 450,
    "total_tokens": 462
  },
  "metadata": {
    "fallback_attempted": false,
    "source": "api",
    "user_id": "user_123"
  },
  "name": "market_analysis",
  "cost": 0.025400
}
```

---

## Alternative Log Formats

### Legacy Format Support
CrashLens also supports logs with slight variations in structure:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "trace_id": "trace_123",
  "model": "gpt-4",
  "prompt_tokens": 150,
  "completion_tokens": 50,
  "prompt": "User input text",
  "completion": "Model response",
  "metadata": {"team": "engineering"}
}
```

**Note:** This format has limited detection capabilities compared to the primary Langfuse format.

---

## Input Methods

### 1. File Input (Primary)
```bash
python -m crashlens scan /path/to/logs.jsonl
```

### 2. Standard Input
```bash
cat logs.jsonl | python -m crashlens scan -
```

### 3. Multiple Files
```bash
python -m crashlens scan logs1.jsonl logs2.jsonl
```

---

## Validation and Error Handling

### Parser Behavior
- **Invalid JSON:** Warns and skips malformed lines
- **Missing Required Fields:** Skips records with missing `traceId` or `type`
- **Wrong Type:** Only processes `type: "generation"` records
- **Empty Files:** Reports warning and exits gracefully

### Common Issues
1. **Missing `traceId`:** Records cannot be grouped for pattern detection
2. **Invalid `type`:** Only `"generation"` records are processed
3. **Missing Token Counts:** Cost calculation will be inaccurate
4. **Invalid Timestamps:** Time-window analysis may fail
5. **Unknown Models:** Uses default pricing, may affect cost accuracy

### Validation Examples
```bash
# Valid processing
✅ Processed 150 records from 25 traces

# Warning examples  
⚠️ Warning: Invalid JSON on line 45: Expecting ',' delimiter
⚠️ Warning: Skipping record without traceId on line 12
⚠️ Warning: Unknown model 'custom-model', using default pricing
```

---

## Best Practices

### Log Structure
1. **Consistent Field Names:** Use exact field names as specified
2. **Complete Usage Data:** Always include `prompt_tokens` and `completion_tokens`
3. **Proper Timestamps:** Use ISO8601 format for all time fields
4. **Meaningful Trace IDs:** Use descriptive trace IDs for easier debugging

### Performance Optimization
1. **File Size:** No strict limits, but files >100MB may be slower to process
2. **Compression:** JSONL files can be compressed for storage
3. **Batch Processing:** Process multiple files separately for better error isolation

### Cost Accuracy
1. **Model Names:** Use exact model names for accurate pricing
2. **Token Counts:** Ensure accurate token counting from your API client
3. **Custom Pricing:** Provide custom pricing config for non-standard models

---

## Summary

CrashLens expects **Langfuse-style JSONL generation logs** with the following critical requirements:

**Minimum Required Fields:**
- `traceId` (string)
- `type` ("generation")
- `input.model` (string)
- `input.prompt` (string)
- `usage.prompt_tokens` (number)
- `usage.completion_tokens` (number)
- `startTime` (ISO8601 string)

**Recommended Additional Fields:**
- `metadata.fallback_attempted` (boolean)
- `level` (string)
- `name` (string)
- `cost` (number)

This format enables comprehensive detection of retry loops, fallback patterns, overkill model usage, and accurate cost calculation for token waste analysis.
