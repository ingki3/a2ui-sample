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
    try {
        const div = document.createElement('div');
        div.className = 'message agent-msg';
        div.style.width = '100%';
        div.style.backgroundColor = 'transparent';
        div.style.padding = '0';

        const surfaceDiv = document.createElement('div');
        surfaceDiv.className = 'a2ui-surface';

        // Process Data Model Updates
        if (a2uiData.dataModelUpdate && a2uiData.dataModelUpdate.contents) {
            a2uiData.dataModelUpdate.contents.forEach(content => {
                if (content && content.valueMap) {
                    content.valueMap.forEach(kv => {
                        const path = `/${content.key}/${kv.key}`;
                        dataStore[path] = kv.valueString;
                    });
                }
            });
        }

        // Render Components
        if (a2uiData.surfaceUpdate && a2uiData.beginRendering) {
            const rootId = a2uiData.beginRendering.root;

            // Safety check for components array
            const compList = a2uiData.surfaceUpdate.components || [];
            const components = new Map(compList.map(c => [c.id, c.component]));

            const renderComponent = (id) => {
                const comp = components.get(id);
                if (!comp) return null;

                if (comp.Text) {
                    const hint = comp.Text.usageHint || 'body';
                    // Safe access to literalString
                    const textObj = comp.Text.text || {};
                    const text = textObj.literalString || '';
                    const url = comp.Text.url ? comp.Text.url.literalString : null;

                    let el;

                    // Handle news-specific styles
                    if (hint === 'news-title' && url) {
                        el = document.createElement('a');
                        el.href = url;
                        el.target = '_blank';
                        el.className = 'a2ui-news-title';
                        el.innerText = text;
                    } else if (hint === 'news-publisher') {
                        el = document.createElement('span');
                        el.className = 'a2ui-news-publisher';
                        el.innerText = text;
                    } else if (hint === 'news-date') {
                        el = document.createElement('span');
                        el.className = 'a2ui-news-date';
                        el.innerText = '• ' + text;
                    } else if (hint === 'news-header-title') {
                        el = document.createElement('h2');
                        el.style.margin = '0';
                        el.style.fontSize = '18px';
                        el.style.fontWeight = '600';
                        el.innerText = text;
                    } else if (hint === 'news-header-subtitle') {
                        el = document.createElement('span');
                        el.style.fontSize = '12px';
                        el.style.opacity = '0.9';
                        el.innerText = text;
                    } else if (hint === 'h2') {
                        el = document.createElement('h2');
                        el.className = 'a2ui-news-title'; // Reuse news title style
                        el.style.fontSize = '18px';
                        el.style.fontWeight = 'bold';
                        el.innerText = text;
                    } else if (hint === 'h3') {
                        el = document.createElement('div');
                        el.style.fontSize = '16px';
                        el.style.fontWeight = 'bold';
                        el.style.color = '#d32f2f'; // Red for price
                        el.innerText = text;
                    } else if (hint === 'h1') {
                        el = document.createElement('h1');
                        el.className = 'a2ui-text-h1';
                        el.innerText = text;
                    } else if (hint === 'caption') {
                        el = document.createElement('div');
                        el.className = 'a2ui-news-date'; // Reuse gray text
                        el.innerText = text;
                    } else if (hint === 'link' && url) {
                        el = document.createElement('a');
                        el.href = url;
                        el.target = '_blank';
                        el.className = `a2ui-text-${hint}`;
                        el.innerText = text;
                    } else {
                        el = document.createElement('div');
                        el.className = `a2ui-text-${hint}`;
                        el.innerText = text;
                    }

                    return el;
                } else if (comp.TextField) {
                    const el = document.createElement('div');
                    el.className = 'a2ui-textfield';

                    const label = document.createElement('label');
                    const labelObj = comp.TextField.label || {};
                    label.innerText = labelObj.literalString || 'Label';
                    el.appendChild(label);

                    const input = document.createElement('input');
                    input.type = 'text';
                    const path = comp.TextField.text ? comp.TextField.text.path : '';
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
                        const childTextObj = childComp.Text.text || {};
                        btn.innerText = childTextObj.literalString || 'Button';
                    } else {
                        btn.innerText = 'Button';
                    }

                    btn.onclick = () => {
                        handleAction(comp.Button.action);
                    };
                    return btn;
                } else if (comp.Column) {
                    const col = document.createElement('div');
                    const style = comp.Column.style || '';

                    // Handle news-specific column styles
                    if (style === 'news-card' || style === 'product-card') {
                        col.className = 'a2ui-news-card';
                    } else if (style === 'news-header') {
                        col.className = 'a2ui-news-header';
                    } else {
                        col.className = 'a2ui-column';
                    }

                    if (comp.Column.children && comp.Column.children.explicitList) {
                        comp.Column.children.explicitList.forEach(childId => {
                            const childEl = renderComponent(childId);
                            if (childEl) col.appendChild(childEl);
                        });
                    }
                    return col;
                } else if (comp.Row) {
                    const row = document.createElement('div');
                    const style = comp.Row.style || '';

                    if (style === 'news-meta') {
                        row.className = 'a2ui-news-meta';
                    } else if (style === 'product-row') {
                        row.className = 'a2ui-row';
                        row.style.display = 'flex';
                        row.style.gap = '10px';
                        row.style.width = '100%';
                    } else {
                        row.className = 'a2ui-row';
                        // Simple flex row style
                        row.style.display = 'flex';
                        row.style.gap = '10px';
                        row.style.alignItems = 'center';
                        row.style.overflowX = 'auto'; // safe for mobile
                    }

                    if (comp.Row.children && comp.Row.children.explicitList) {
                        comp.Row.children.explicitList.forEach(childId => {
                            const childEl = renderComponent(childId);
                            if (childEl) {
                                if (style === 'product-row') {
                                    childEl.style.flex = '1';
                                    childEl.style.minWidth = '0'; // Prevent overflow
                                }
                                row.appendChild(childEl);
                            }
                        });
                    }
                    return row;
                } else if (comp.Image) {
                    const img = document.createElement('img');
                    img.className = 'a2ui-image';
                    const urlObj = comp.Image.url || {};
                    img.src = urlObj.literalString || '';
                    const altObj = comp.Image.altText || {};
                    img.alt = altObj.literalString || 'Image';
                    img.style.maxWidth = '100%';
                    img.style.borderRadius = '8px';
                    return img;
                } else if (comp.IFrame) {
                    const iframe = document.createElement('iframe');
                    iframe.className = 'a2ui-iframe';
                    const urlObj = comp.IFrame.url || {};
                    iframe.src = urlObj.literalString;
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

                    setTimeout(() => {
                        try {
                            if (typeof LightweightCharts === 'undefined') {
                                console.error("LightweightCharts is not loaded.");
                                return;
                            }
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
                        } catch (e) { console.error("Chart Error", e); }
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
    } catch (e) {
        console.error("UI Render Error:", e);
        addMessage(`[System Error: Failed to render UI components. ${e.message}]`, false);
    }
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

        let buffer = '';
        let currentEvent = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            const lines = buffer.split('\n');
            // Keep the last part in buffer as it might be incomplete
            // unless the buffer ended with \n, in which case the last element is empty string
            buffer = lines.pop();

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine) {
                    // Empty line means end of event (if we were strictly parsing blocks)
                    // But here we handle lines directly
                    continue;
                }

                if (trimmedLine.startsWith('event: ')) {
                    currentEvent = trimmedLine.slice(7).trim();
                } else if (trimmedLine.startsWith('data: ')) {
                    if (!currentEvent) continue; // ignore data without event

                    try {
                        const dataStr = trimmedLine.slice(6);
                        const data = JSON.parse(dataStr);

                        if (currentEvent === 'a2ui') {
                            addA2UIWidget(data.data);
                        } else if (currentEvent === 'text') {
                            // Streaming text
                            accumulatedText += data.text;
                            if (!streamingTextDiv) {
                                streamingTextDiv = document.createElement('div');
                                streamingTextDiv.className = 'message agent-msg';
                                messagesDiv.appendChild(streamingTextDiv);
                            }
                            streamingTextDiv.textContent = accumulatedText;
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        } else if (currentEvent === 'done') {
                            // Done
                        }
                    } catch (err) {
                        console.error('Error parsing SSE data:', err);
                    }
                    // We don't reset currentEvent here because standard SSE might have multiple data lines for one event,
                    // though our server sends event/data pairs. 
                    // Resetting it or keeping it doesn't matter much if we always send event: before data:
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
