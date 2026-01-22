# A2UI Implementation Guide

이 문서는 A2UI(Agentic AI User Interface)의 구현 방식을 상세히 설명합니다.

## 1. 아키텍처 개요

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▸│   Server    │───▸│     LLM     │───▸│  Tool Call  │
│ (renderer)  │◂───│  (FastAPI)  │◂───│  (Gemini)   │◂───│  Execution  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                   │                                      │
      │                   └──────────────────────────────────────┘
      │                              A2UI JSON Response
      ▼
┌─────────────┐
│  Dynamic UI │
│  Rendering  │
└─────────────┘
```

## 2. LLM Function Calling

### 2.1 도구 정의 (`llm_wrapper.py`)

```python
auth_tool = {
    "function_declarations": [
        {
            "name": "get_stock_chart",
            "description": "Get the stock price history chart for a given symbol.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "symbol": {
                        "type": "STRING",
                        "description": "The stock symbol (e.g. AAPL, GOOG, TSLA)."
                    }
                },
                "required": ["symbol"]
            }
        }
    ]
}
```

### 2.2 LLM 응답 처리

```python
def process_query(self, text: str) -> Dict[str, Any]:
    response = self.chat.send_message(text)
    
    tool_calls = []
    for part in response.parts:
        if fn := part.function_call:
            tool_calls.append({
                "tool_name": fn.name,
                "tool_args": dict(fn.args)
            })
    
    if tool_calls:
        return {"type": "multiple_tool_calls", "calls": tool_calls}
    else:
        return {"type": "text", "text": response.text}
```

### 2.3 시스템 프롬프트

LLM이 질문 없이 바로 도구를 호출하도록 설정:

```python
system_instruction="""You are a helpful assistant that uses tools to fulfill user requests.

IMPORTANT RULES:
1. When the user asks for something that can be done with a tool, ALWAYS call the tool immediately.
2. Do NOT ask clarifying questions - use reasonable defaults if optional parameters are not specified.
3. Prefer action over conversation."""
```

## 3. A2UI JSON 구조

### 3.1 전체 응답 구조

```json
{
  "kind": "a2ui",
  "data": {
    "surfaceUpdate": {
      "surfaceId": "stock_chart",
      "components": [...]
    },
    "dataModelUpdate": {
      "surfaceId": "stock_chart",
      "contents": [...]
    },
    "beginRendering": {
      "surfaceId": "stock_chart",
      "root": "root_component_id"
    }
  }
}
```

#### 각 Entity 역할 설명

| Entity | 역할 | 상세 설명 |
|--------|------|----------|
| `kind` | 응답 타입 식별 | `"a2ui"`: A2UI UI 응답, `"text"`: 일반 텍스트 응답. 클라이언트가 어떻게 렌더링할지 결정 |
| `data` | A2UI 페이로드 컨테이너 | 모든 UI 관련 데이터를 담는 최상위 객체 |

#### `surfaceUpdate` (UI 컴포넌트 정의)

```json
"surfaceUpdate": {
  "surfaceId": "stock_chart",
  "components": [
    {"id": "root", "component": {"Column": {...}}},
    {"id": "title", "component": {"Text": {...}}}
  ]
}
```

| 필드 | 역할 |
|------|------|
| `surfaceId` | UI 영역 식별자. 동일 surfaceId는 같은 영역을 업데이트 |
| `components` | 렌더링할 컴포넌트 배열. 각 컴포넌트는 `id`와 `component` 타입을 가짐 |

#### `dataModelUpdate` (동적 데이터 바인딩)

```json
"dataModelUpdate": {
  "surfaceId": "stock_chart",
  "contents": [
    {"path": "loanAmount", "value": {"stringValue": "10000"}}
  ]
}
```

| 필드 | 역할 |
|------|------|
| `surfaceId` | 데이터가 적용될 UI 영역 |
| `contents` | 데이터 바인딩 배열. `TextField`의 `dataSourcePath`와 연결되어 양방향 데이터 동기화 |

**사용 예**: 대출 계산기에서 사용자가 입력한 값을 `dataModelUpdate`를 통해 서버로 전송하고, 계산 결과를 다시 받아 UI에 표시.

#### `beginRendering` (렌더링 시작점)

```json
"beginRendering": {
  "surfaceId": "stock_chart",
  "root": "chart_root"
}
```

| 필드 | 역할 |
|------|------|
| `surfaceId` | 렌더링할 UI 영역 |
| `root` | 렌더링 시작점이 될 최상위 컴포넌트의 ID. 이 컴포넌트부터 자식들을 재귀적으로 렌더링 |

**렌더링 흐름**:
1. 클라이언트가 `beginRendering.root` ID 확인
2. `components`에서 해당 ID 찾기
3. 컴포넌트가 `Column`/`Row`면 `children.explicitList`의 자식들을 재귀 렌더링

### 3.2 컴포넌트 타입 (`models.py`)

| 컴포넌트 | 설명 | 주요 속성 |
|---------|------|----------|
| `Text` | 텍스트 표시 | `text`, `usageHint` |
| `TextField` | 입력 필드 | `label`, `dataSourcePath` |
| `Button` | 버튼 | `child`, `action` |
| `Column` | 세로 배치 | `children.explicitList` |
| `Row` | 가로 배치 | `children.explicitList` |
| `Image` | 이미지 | `url`, `altText` |
| `Chart` | 차트 | `data`, `color` |
| `IFrame` | 임베드 | `url`, `height` |

### 3.3 컴포넌트 예시

```json
{
  "id": "chart_1",
  "component": {
    "Chart": {
      "data": [
        {"time": "2024-01-15", "value": 185.92},
        {"time": "2024-01-16", "value": 188.63}
      ],
      "color": "#0F9D58"
    }
  }
}
```

## 4. 서버 구현 (`main.py`)

### 4.1 SSE 스트리밍 엔드포인트

```python
@app.post("/chat/stream")
async def chat_stream(request: Request, chat_req: ChatRequest):
    async def event_generator():
        processed = llm.process_query(text)
        
        for call in processed["calls"]:
            if call["tool_name"] == "get_stock_chart":
                res = stock_service.get_stock_chart(symbol)
                
                # A2UI 응답 전송
                yield f"event: a2ui\ndata: {json.dumps(res.model_dump())}\n\n"
                
                # 스트리밍 코멘터리
                async for chunk in llm.generate_commentary_stream(symbol, price):
                    yield f"event: text\ndata: {json.dumps({'text': chunk})}\n\n"
        
        yield f"event: done\ndata: {{}}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 4.2 도구 실행 흐름

1. LLM이 `tool_name`과 `tool_args` 반환
2. 서비스 클래스의 해당 메서드 호출
3. Jinja2 템플릿으로 A2UI JSON 생성
4. SSE로 클라이언트에 전송

## 5. 템플릿 시스템 (`templates/`)

### 5.1 템플릿 구조

```jinja2
{
  "surfaceUpdate": {
    "components": [
      {% for r in restaurants %}
      {
        "id": "{{ uid }}_item_{{ loop.index }}",
        "component": {
          "Text": { "text": { "literalString": "{{ r.name }}" } }
        }
      }
      {% endfor %}
    ]
  }
}
```

### 5.2 UID (Unique ID) 생성

멀티 인텐트 지원을 위해 각 컴포넌트에 고유 UID 부여:

```python
import uuid
uid = str(uuid.uuid4())[:8]
return self._render_template("template.json.j2", {"uid": uid, **context})
```

## 6. 클라이언트 렌더링 (`renderer.js`)

### 6.1 SSE 이벤트 처리

```javascript
const response = await fetch('/chat/stream', { method: 'POST', ... });
const reader = response.body.getReader();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    // 이벤트 파싱
    if (eventType === 'a2ui') {
        addA2UIWidget(data.data);
    } else if (eventType === 'text') {
        // 스트리밍 텍스트 표시
        streamingTextDiv.textContent += data.text;
    }
}
```

### 6.2 재귀적 컴포넌트 렌더링

```javascript
function renderComponent(id) {
    const entry = componentMap[id];
    const comp = entry.component;
    
    if (comp.Text) {
        const el = document.createElement('span');
        el.textContent = comp.Text.text.literalString;
        return el;
    } else if (comp.Column) {
        const col = document.createElement('div');
        comp.Column.children.explicitList.forEach(childId => {
            col.appendChild(renderComponent(childId));  // 재귀 호출
        });
        return col;
    }
    // ... 다른 컴포넌트 타입
}
```

## 7. 외부 API 연동

### 7.1 Naver Local Search API

```python
def _search_naver_local(self, query: str) -> list:
    url = f"https://openapi.naver.com/v1/search/local.xml?query={quote(query)}"
    headers = {
        "X-Naver-Client-Id": self.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": self.NAVER_CLIENT_SECRET
    }
    response = httpx.get(url, headers=headers)
    # XML 파싱 및 데이터 추출
```

### 7.2 yfinance (주식 데이터)

```python
def get_stock_chart(self, symbol: str):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1y")
    prices = [{"time": date.strftime("%Y-%m-%d"), "value": float(close)} 
              for date, close in hist['Close'].items()]
```

## 8. 멀티 인텐트 지원

"애플이랑 엔비디아 주가 알려줘" 같은 복합 요청 처리:

```python
# LLM이 multiple_tool_calls 반환
{
    "type": "multiple_tool_calls",
    "calls": [
        {"tool_name": "get_stock_chart", "tool_args": {"symbol": "AAPL"}},
        {"tool_name": "get_stock_chart", "tool_args": {"symbol": "NVDA"}}
    ]
}
```

서버가 각 호출을 순차적으로 처리하고 별도의 A2UI 이벤트로 전송.

## 9. Button Action과 Server Roundtrip

### 9.1 대출 계산기 재계산 흐름

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   클라이언트   │────▸│    서버      │────▸│   재계산     │
│  (버튼 클릭)  │◂────│  (FastAPI)   │◂────│   처리       │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │ 1. action 전송     │                    │
       │   + context data   │                    │
       │                    │ 2. 계산 수행       │
       │                    │                    │
       │ 4. 새 A2UI 응답    │ 3. 새 UI 생성      │
       ◂────────────────────┘                    │
```

### 9.2 버튼 컴포넌트 구조

```json
{
  "id": "calc_button",
  "component": {
    "Button": {
      "child": "calc_button_text",
      "action": {
        "name": "calculateLoan",
        "context": [
          { "key": "principal", "value": { "path": "/calculator/principal" } },
          { "key": "annualRate", "value": { "path": "/calculator/rate" } },
          { "key": "years", "value": { "path": "/calculator/years" } }
        ]
      }
    }
  }
}
```

**핵심 개념**:
- `action.name`: 서버에서 실행할 액션 이름
- `context`: 액션에 전달할 파라미터 (데이터 바인딩 path 참조)

### 9.3 Server Roundtrip이 필요한 이유

> **질문**: 버튼 클릭 시 서버 라운드트립이 필요한 것이 A2UI 특성인가, 아니면 구현 선택인가?

#### A2UI 프로토콜 특성 (본질적 설계)

| 특성 | 설명 |
|------|------|
| **선언적 UI** | 서버가 UI 구조를 완전히 정의, 클라이언트는 렌더러 역할만 |
| **서버 중심 로직** | 비즈니스 로직(계산, 검증)은 서버에서 수행 |
| **상태 동기화** | 데이터 변경 시 서버에서 새 UI 상태를 생성하여 전송 |

#### 현재 구현의 선택

```javascript
// renderer.js의 handleAction 함수
function handleAction(action) {
    // 서버로 액션 전송
    fetch('/action', {
        method: 'POST',
        body: JSON.stringify({
            name: action.name,
            context: resolvedContext  // dataStore에서 값 해석
        })
    });
}
```

| 구현 선택 | 대안 (A2UI에서도 가능) |
|----------|----------------------|
| 모든 계산을 서버에서 수행 | 간단한 계산은 클라이언트 JavaScript로 처리 |
| 전체 UI를 새로 렌더링 | `surfaceId` 기반 부분 업데이트 |

### 9.4 A2UI 특성 vs 구현 선택 비교

| 항목 | A2UI 프로토콜 특성 | 현재 구현의 선택 |
|------|-------------------|-----------------|
| UI 정의 위치 | ✅ 서버에서 JSON으로 정의 | - |
| 버튼 액션 정의 | ✅ `action.name`과 `context`로 정의 | - |
| 데이터 바인딩 | ✅ `path` 기반 양방향 바인딩 | - |
| 계산 로직 위치 | 프로토콜 미지정 | 🔧 서버에서 수행 |
| UI 업데이트 방식 | 프로토콜 미지정 | 🔧 전체 재렌더링 |
| 클라이언트 로컬 계산 | 프로토콜에서 허용 | 🔧 미사용 |

### 9.5 클라이언트 로컬 계산 (가능한 대안)

A2UI는 클라이언트 측 계산을 금지하지 않습니다. 다음과 같이 구현할 수도 있습니다:

```javascript
// 클라이언트 측 계산 (선택적 구현)
if (action.name === 'calculateLoan' && action.localCompute) {
    const principal = parseFloat(dataStore['/calculator/principal']);
    const rate = parseFloat(dataStore['/calculator/rate']);
    const years = parseInt(dataStore['/calculator/years']);
    
    // 로컬 계산
    const monthlyRate = rate / 100 / 12;
    const months = years * 12;
    const monthly = principal * monthlyRate / (1 - Math.pow(1 + monthlyRate, -months));
    
    // UI 직접 업데이트 (서버 없이)
    updateResultDisplay(monthly);
}
```

**하지만 서버 라운드트립을 사용하는 이유**:
1. **일관성**: 복잡한 비즈니스 로직을 서버에서 중앙 관리
2. **보안**: 민감한 계산 로직 보호
3. **유연성**: 서버에서 추가 정보(비교 데이터 등) 제공 가능
4. **단순성**: 클라이언트 렌더러를 단순하게 유지

### 9.6 결론

| 질문 | 답변 |
|------|------|
| 서버 라운드트립은 A2UI 필수인가? | ❌ 아니오, 프로토콜 특성이 아닌 **구현 선택** |
| A2UI가 서버 중심 설계를 권장하는가? | ✅ 예, 하지만 강제하지는 않음 |
| 현재 구현이 합리적인가? | ✅ 예, 서버 중심 접근은 복잡한 앱에 적합 |

## 10. 파일 구조

```
a2ui/
├── main.py              # FastAPI 서버, 엔드포인트 정의
├── agent.py             # 서비스 클래스 (도구 구현)
├── llm_wrapper.py       # LLM 통신, Function Calling
├── models.py            # Pydantic 모델 (A2UI 스키마)
├── templates/           # Jinja2 템플릿 (A2UI JSON)
│   ├── stock_chart.json.j2
│   └── restaurant_list.json.j2
└── static/
    ├── index.html       # 클라이언트 HTML
    └── renderer.js      # A2UI 렌더러
```
