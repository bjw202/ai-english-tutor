# Implementation Plan: SPEC-GLM-001

## Metadata

| Field | Value |
|-------|-------|
| SPEC ID | SPEC-GLM-001 |
| Title | GLM Model Migration Implementation Plan |
| Created | 2026-02-23 |
| Methodology | Hybrid (TDD for new code, DDD for existing modifications) |

---

## 1. Implementation Overview

### 1.1 Approach

This migration follows the **Hybrid methodology**:
- **TDD** for new GLM routing logic in `llm.py`
- **DDD** for modifications to existing agent files (preserve behavior, then improve)
- **Incremental rollout** with environment variable-based rollback capability

### 1.2 Success Metrics

- All 8 files modified successfully
- All unit tests pass (100%)
- All integration tests pass (100%)
- Manual testing confirms Korean content quality
- Cost reduction of 70-90% verified

---

## 2. Milestones

### Milestone 1: Foundation (Priority High)

**Goal**: Set up infrastructure for GLM integration

**Tasks**:
1. Add `zhipuai` dependency to `pyproject.toml`
2. Add GLM configuration fields to `config.py`
3. Update `.env.example` with GLM configuration

**Deliverables**:
- Updated `pyproject.toml` with zhipuai>=2.0.0,<3.0.0
- Extended `Settings` class with GLM_API_KEY and GLM_BASE_URL
- Complete `.env.example` with GLM configuration examples

**Verification**:
- `uv sync` completes successfully
- Settings class accepts GLM environment variables
- Configuration loads without errors

---

### Milestone 2: Core Integration (Priority High)

**Goal**: Implement GLM model routing in LLM factory

**Tasks**:
1. Add GLM routing logic to `get_llm()` function
2. Write unit tests for GLM model initialization
3. Test error handling for missing GLM_API_KEY

**Deliverables**:
- Modified `llm.py` with GLM support
- Unit tests in `test_llm.py` covering GLM models
- Error messages for configuration issues

**Technical Design**:

```python
def get_llm(model_name: str, max_tokens: int | None = None, timeout: int = 120) -> BaseChatModel:
    settings = get_settings()

    # GLM models (NEW)
    if model_name.startswith("glm-"):
        if not settings.GLM_API_KEY:
            raise ValueError("GLM_API_KEY is required for GLM models")
        return ChatOpenAI(
            model=model_name,
            base_url=settings.GLM_BASE_URL,
            api_key=settings.GLM_API_KEY,
            timeout=timeout,
            max_retries=2,
            max_tokens=max_tokens if max_tokens is not None else 4096,
        )

    # Existing OpenAI routing...
    # Existing Anthropic routing...
```

**Verification**:
- Unit tests pass for GLM-4-flash and GLM-4-plus
- Error handling works correctly
- Integration with LangChain validated

---

### Milestone 3: Agent Migration (Priority High)

**Goal**: Migrate all agents to use configuration-driven model selection

**Tasks**:
1. Modify `supervisor.py` to use `settings.SUPERVISOR_MODEL`
2. Modify `grammar.py` to use `settings.GRAMMAR_MODEL`
3. Modify `reading.py` to use `settings.READING_MODEL`
4. Modify `vocabulary.py` to use `settings.VOCABULARY_MODEL`
5. Update unit tests for each agent

**Deliverables**:
- 4 agent files with configuration-based model selection
- Updated unit tests reflecting changes
- No hardcoded model names in agent code

**Pattern (applied to all agents)**:

```python
# Before
llm = get_llm("claude-haiku-4-5", max_tokens=1024, timeout=30)

# After
from tutor.config import get_settings
settings = get_settings()
llm = get_llm(settings.SUPERVISOR_MODEL, max_tokens=1024, timeout=30)
```

**Verification**:
- All agent unit tests pass
- Agents work with both original and GLM models
- No regression in functionality

---

### Milestone 4: Testing & Validation (Priority High)

**Goal**: Comprehensive testing across all model combinations

**Tasks**:
1. Run full unit test suite with original models
2. Run full unit test suite with GLM models
3. Run integration tests with original models
4. Run integration tests with GLM models
5. Manual testing of all features with GLM models

**Test Scenarios**:

| Scenario | Model Config | Expected Result |
|----------|-------------|-----------------|
| Text analysis | GLM all agents | Korean explanations generated |
| Image analysis | GLM all agents | OCR + Korean explanations |
| Long text | GLM all agents | Successful chunking and processing |
| Error handling | GLM invalid key | Clear error message |
| Rollback | OpenAI/Anthropic | Original behavior restored |

**Verification**:
- 100% unit test pass rate
- 100% integration test pass rate
- Manual QA sign-off

---

### Milestone 5: Documentation & Deployment (Priority Medium)

**Goal**: Document changes and prepare for production deployment

**Tasks**:
1. Update README with GLM configuration instructions
2. Update CHANGELOG with migration details
3. Create migration guide for team members
4. Prepare rollback procedure documentation

**Deliverables**:
- Updated README.md
- CHANGELOG entry
- Migration guide in `.moai/docs/`
- Rollback procedure document

**Rollback Procedure**:

```bash
# Emergency rollback (1 minute)
# 1. Update .env file
SUPERVISOR_MODEL=gpt-4o-mini
GRAMMAR_MODEL=gpt-4o
READING_MODEL=claude-sonnet-4-5
VOCABULARY_MODEL=claude-haiku-4-5

# 2. Restart service
uv run uvicorn tutor.main:app --reload
```

**Verification**:
- Documentation reviewed and approved
- Rollback procedure tested

---

## 3. Technical Approach

### 3.1 LLM Factory Enhancement

**Current State**:
- Routes based on prefix: "gpt-" → OpenAI, "claude-" → Anthropic
- Throws ValueError for unknown prefixes

**Target State**:
- Add "glm-" prefix routing to GLM API
- Use ChatOpenAI with custom base_url for GLM
- Maintain existing behavior for OpenAI/Anthropic

**Implementation Strategy**:
1. Add GLM routing before existing routing logic
2. Validate GLM_API_KEY presence
3. Use GLM_BASE_URL from settings (with default)
4. Apply same timeout and retry logic as other providers

### 3.2 Configuration Management

**New Environment Variables**:

```bash
# GLM API Configuration
GLM_API_KEY=your_glm_api_key_here          # Required for GLM models
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/  # Optional, has default

# Model Selection (migrate to GLM)
SUPERVISOR_MODEL=glm-4-flash
GRAMMAR_MODEL=glm-4-plus
READING_MODEL=glm-4-plus
VOCABULARY_MODEL=glm-4-flash
```

**Settings Class Extensions**:

```python
class Settings(BaseSettings):
    # Existing...
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # New GLM fields
    GLM_API_KEY: str = ""
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"

    # Model configuration
    SUPERVISOR_MODEL: str = "gpt-4o-mini"
    GRAMMAR_MODEL: str = "gpt-4o"
    READING_MODEL: str = "claude-sonnet-4-5"
    VOCABULARY_MODEL: str = "claude-haiku-4-5"
```

### 3.3 Dependency Management

**pyproject.toml Addition**:

```toml
[project.dependencies]
# Existing dependencies...
langchain-openai = ">=0.3.0,<0.4.0"
langchain-anthropic = ">=0.3.0,<0.4.0"

# New GLM dependency
zhipuai = ">=2.0.0,<3.0.0"
```

**Note**: While we use LangChain's ChatOpenAI for GLM (OpenAI-compatible), adding zhipuai ensures we have the latest API compatibility information and can use official SDK if needed.

---

## 4. Architecture Decisions

### 4.1 Why ChatOpenAI for GLM?

**Decision**: Use LangChain's ChatOpenAI with custom base_url instead of zhipuai SDK

**Rationale**:
1. **Consistency**: Same interface as OpenAI integration
2. **Simplicity**: No new abstraction layer needed
3. **Compatibility**: GLM API is OpenAI-compatible
4. **Maintainability**: Fewer dependencies to manage

**Trade-offs**:
- (+) Minimal code changes
- (+) Easy rollback
- (+) Consistent error handling
- (-) May miss GLM-specific features (acceptable for MVP)

### 4.2 Configuration-Driven Model Selection

**Decision**: Use environment variables for model selection per agent

**Rationale**:
1. **Flexibility**: Easy to switch models without code changes
2. **Rollback**: Simple environment variable change
3. **Testing**: Can test with different model combinations
4. **A/B Testing**: Potential for gradual rollout

**Trade-offs**:
- (+) No code changes for model switching
- (+) Environment-specific configuration
- (-) Requires deployment for model changes (acceptable)

---

## 5. Risk Mitigation

### 5.1 Technical Risks

| Risk | Mitigation Strategy |
|------|---------------------|
| GLM API downtime | Keep OpenAI/Anthropic configuration ready for instant rollback |
| Poor content quality | Manual QA testing with Korean native speakers |
| Integration bugs | Comprehensive unit and integration tests |
| Performance issues | Load testing with GLM API before full migration |

### 5.2 Rollback Strategy

**Immediate Rollback (< 1 minute)**:
1. Update .env file with original model names
2. Restart application
3. Verify original functionality

**Code Rollback**:
```bash
git checkout main
git branch -D feature/glm-migration
```

**Partial Rollback**:
- Keep some agents on GLM, revert others via individual MODEL settings

---

## 6. Testing Strategy

### 6.1 Unit Testing

**Test Coverage Requirements**:
- GLM model initialization in `llm.py`
- Configuration loading in `config.py`
- Agent model selection in agent files
- Error handling for missing API keys

**Test Cases**:

```python
# test_llm.py additions
def test_get_llm_glm_flash():
    """Test GLM-4-flash model initialization."""
    with mock.patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
        llm = get_llm("glm-4-flash")
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "glm-4-flash"

def test_get_llm_glm_plus():
    """Test GLM-4-plus model initialization."""
    with mock.patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
        llm = get_llm("glm-4-plus")
        assert isinstance(llm, ChatOpenAI)

def test_get_llm_glm_missing_api_key():
    """Test error when GLM_API_KEY is missing."""
    with mock.patch.dict(os.environ, {"GLM_API_KEY": ""}):
        with pytest.raises(ValueError, match="GLM_API_KEY is required"):
            get_llm("glm-4-flash")
```

### 6.2 Integration Testing

**Test Scenarios**:
1. Full text analysis flow with GLM models
2. Image analysis (OCR + text analysis) with GLM models
3. Multi-turn conversation with GLM models
4. Error recovery with GLM API failures
5. Performance benchmarking (response time comparison)

### 6.3 Manual Testing

**QA Checklist**:
- [ ] Korean grammar explanations are accurate
- [ ] Slash reading training is natural
- [ ] Etymology explanations are correct
- [ ] Difficulty level adaptation works correctly
- [ ] Response quality matches or exceeds original models
- [ ] No errors in production logs

---

## 7. Deployment Checklist

### 7.1 Pre-Deployment

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual QA completed
- [ ] Documentation updated
- [ ] Team review completed
- [ ] Rollback procedure tested

### 7.2 Deployment Steps

1. **Feature Branch Merge**:
   ```bash
   git checkout main
   git pull origin main
   git merge feature/glm-migration
   git push origin main
   ```

2. **Environment Configuration**:
   - Add GLM_API_KEY to production environment
   - Verify GLM_BASE_URL is correct
   - Update model settings to GLM models

3. **Service Deployment**:
   - Deploy backend with new code
   - Monitor logs for errors
   - Verify health check endpoint

4. **Smoke Testing**:
   - Test text analysis feature
   - Test image analysis feature
   - Verify Korean content quality

### 7.3 Post-Deployment

- [ ] Monitor error rates for 24 hours
- [ ] Monitor response times
- [ ] Check cost metrics
- [ ] Gather user feedback
- [ ] Document any issues

---

## 8. Timeline

### Estimated Effort

| Milestone | Effort | Dependencies |
|-----------|--------|--------------|
| Foundation | 1 hour | None |
| Core Integration | 2 hours | Foundation |
| Agent Migration | 2 hours | Core Integration |
| Testing & Validation | 3 hours | Agent Migration |
| Documentation & Deployment | 1 hour | Testing & Validation |

**Total Estimated Effort**: 9 hours

### Critical Path

Foundation → Core Integration → Agent Migration → Testing → Deployment

---

## 9. Next Steps

1. **Immediate**: Create feature branch `feature/glm-migration`
2. **Phase 1**: Implement Foundation milestone
3. **Phase 2**: Implement Core Integration with TDD
4. **Phase 3**: Migrate agents with DDD approach
5. **Phase 4**: Execute comprehensive testing
6. **Phase 5**: Deploy to production with monitoring
