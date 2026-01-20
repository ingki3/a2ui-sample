const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const uiModeToggle = document.getElementById('ui-mode-toggle');

// State for data bindings (very simple global store)
let dataStore = {};

function addMessage(text, isUser) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user-msg' : 'agent-msg'}`;
    div.textContent = text;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addA2UIWidget(a2uiData) {
    const div = document.createElement('div');
    div.className = 'message agent-msg';
    div.style.width = '100%';
    div.style.backgroundColor = 'transparent';
    div.style.padding = '0';

    const surfaceDiv = document.createElement('div');
    surfaceDiv.className = 'a2ui-surface';

    // Process Data Model Updates
    if (a2uiData.dataModelUpdate) {
        a2uiData.dataModelUpdate.contents.forEach(content => {
            // Mocking standard path binding: /calculator/{key}
            // content.valueMap is list of {key, valueString}
            content.valueMap.forEach(kv => {
                const path = `/${content.key}/${kv.key}`;
                dataStore[path] = kv.valueString;
            });
        });
    }

    // Render Components
    if (a2uiData.surfaceUpdate && a2uiData.beginRendering) {
        const rootId = a2uiData.beginRendering.root;
        const components = new Map(a2uiData.surfaceUpdate.components.map(c => [c.id, c.component]));

        const renderComponent = (id) => {
            const comp = components.get(id);
            if (!comp) return null;

            if (comp.Text) {
                const el = document.createElement('div');
                const hint = comp.Text.usageHint || 'body';
                el.className = `a2ui-text-${hint}`;
                el.innerText = comp.Text.text.literalString || '';
                return el;
            } else if (comp.TextField) {
                const el = document.createElement('div');
                el.className = 'a2ui-textfield';

                const label = document.createElement('label');
                label.innerText = comp.TextField.label.literalString;
                el.appendChild(label);

                const input = document.createElement('input');
                input.type = 'text';
                const path = comp.TextField.text.path;
                input.value = dataStore[path] || '';
                input.oninput = (e) => {
                    dataStore[path] = e.target.value;
                };
                el.appendChild(input);
                return el;
            } else if (comp.Button) {
                const btn = document.createElement('button');
                btn.className = 'a2ui-button';
                // Find child text for button label
                const childId = comp.Button.child;
                const childComp = components.get(childId);
                if (childComp && childComp.Text) {
                    btn.innerText = childComp.Text.text.literalString;
                } else {
                    btn.innerText = 'Button';
                }

                btn.onclick = () => {
                    handleAction(comp.Button.action);
                };
                return btn;
            } else if (comp.Column) {
                const col = document.createElement('div');
                col.className = 'a2ui-column';
                comp.Column.children.explicitList.forEach(childId => {
                    const childEl = renderComponent(childId);
                    if (childEl) col.appendChild(childEl);
                });
                return col;
            } else if (comp.Row) {
                const row = document.createElement('div');
                row.className = 'a2ui-row';
                // Simple flex row style
                row.style.display = 'flex';
                row.style.gap = '10px';
                row.style.alignItems = 'center';
                row.style.overflowX = 'auto'; // safe for mobile

                comp.Row.children.explicitList.forEach(childId => {
                    const childEl = renderComponent(childId);
                    if (childEl) row.appendChild(childEl);
                });
                return row;
            } else if (comp.Image) {
                const img = document.createElement('img');
                img.className = 'a2ui-image';
                img.src = comp.Image.url.literalString;
                img.alt = comp.Image.altText ? comp.Image.altText.literalString : 'Image';
                img.style.maxWidth = '100%';
                img.style.borderRadius = '8px';
                return img;
            } else if (comp.IFrame) {
                const iframe = document.createElement('iframe');
                iframe.className = 'a2ui-iframe';
                iframe.src = comp.IFrame.url.literalString;
                iframe.style.width = comp.IFrame.width || '100%';
                iframe.style.height = (comp.IFrame.height || 300) + 'px';
                iframe.style.border = 'none';
                iframe.style.borderRadius = '8px';
                iframe.setAttribute('loading', 'lazy');
                iframe.setAttribute('allowfullscreen', '');
                iframe.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
                return iframe;
            } else if (comp.Chart) {
                const chartContainer = document.createElement('div');
                chartContainer.className = 'a2ui-chart';
                chartContainer.style.width = '100%';
                chartContainer.style.height = '300px'; // Increased height for better visibility
                chartContainer.style.padding = '10px 0';

                const data = comp.Chart.data || [];
                if (data.length < 2) return chartContainer;

                // Wait for container to be in DOM to render correctly (or render immediately and resize)
                // Since we are returning the element, we might need a small timeout or IntersectionObserver,
                // but usually LightweightCharts works if we create it.
                // However, the container needs dimensions. We set explicit height. width is 100%.

                setTimeout(() => {
                    const chart = LightweightCharts.createChart(chartContainer, {
                        width: chartContainer.clientWidth,
                        height: 300,
                        layout: {
                            background: { type: 'solid', color: 'transparent' },
                            textColor: '#333',
                        },
                        grid: {
                            vertLines: { color: '#eee' },
                            horzLines: { color: '#eee' },
                        },
                    });

                    const areaSeries = chart.addSeries(LightweightCharts.AreaSeries, {
                        lineColor: comp.Chart.color || '#2962FF',
                        topColor: (comp.Chart.color || '#2962FF') + '66', // Add transparency
                        bottomColor: (comp.Chart.color || '#2962FF') + '04',
                    });

                    areaSeries.setData(data); // data is already in { time, value } format

                    chart.timeScale().fitContent();

                    // Handle resize
                    const resizeObserver = new ResizeObserver(entries => {
                        if (entries.length === 0 || !entries[0].contentRect) return;
                        const newRect = entries[0].contentRect;
                        if (newRect.width > 0) {
                            chart.applyOptions({ width: newRect.width });
                        }
                    });
                    resizeObserver.observe(chartContainer);
                }, 100);

                return chartContainer;
            }
            return null;
        };

        const rootEl = renderComponent(rootId);
        if (rootEl) surfaceDiv.appendChild(rootEl);
    }

    div.appendChild(surfaceDiv);
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function handleAction(action) {
    if (action.name === 'calculateLoan') {
        // Collect context values from store
        const context = {};
        action.context.forEach(ctx => {
            if (ctx.value.path) {
                context[ctx.key] = dataStore[ctx.value.path];
            }
        });

        addMessage(`Recalculating...`, true);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Client-A2UI': 'true' // Always true for button clicks in UI
                },
                body: JSON.stringify({
                    text: 'recalculate', // Dummy text
                    client_context: context
                })
            });
            const data = await response.json();
            if (data.kind === 'a2ui') {
                addA2UIWidget(data.data);
            } else {
                addMessage(data.text || 'Error', false);
            }
        } catch (e) {
            console.error(e);
            addMessage('Error connecting to server', false);
        }
    }
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, true);
    userInput.value = '';

    const isUiMode = uiModeToggle.checked;

    try {
        // Use streaming endpoint
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Client-A2UI': isUiMode ? 'true' : 'false'
            },
            body: JSON.stringify({ text: text })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let streamingTextDiv = null; // For accumulating streaming text
        let accumulatedText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            let eventType = null;

            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    eventType = line.slice(7).trim();
                } else if (line.startsWith('data: ') && eventType) {
                    const data = JSON.parse(line.slice(6));

                    if (eventType === 'a2ui') {
                        addA2UIWidget(data.data);
                    } else if (eventType === 'text') {
                        // Streaming text - accumulate and display
                        accumulatedText += data.text;

                        if (!streamingTextDiv) {
                            streamingTextDiv = document.createElement('div');
                            streamingTextDiv.className = 'message agent-msg streaming-text';
                            messagesDiv.appendChild(streamingTextDiv);
                        }
                        streamingTextDiv.textContent = accumulatedText;
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    } else if (eventType === 'done') {
                        // Finalize streaming
                        if (streamingTextDiv) {
                            streamingTextDiv.classList.remove('streaming-text');
                        }
                    }

                    eventType = null;
                }
            }
        }
    } catch (e) {
        console.error(e);
        addMessage('Error connecting to server', false);
    }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
