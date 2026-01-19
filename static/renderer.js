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
            } else if (comp.Chart) {
                const chartContainer = document.createElement('div');
                chartContainer.className = 'a2ui-chart';
                chartContainer.style.width = '100%';
                chartContainer.style.height = '200px';
                chartContainer.style.padding = '10px 0';

                const data = comp.Chart.data || [];
                if (data.length < 2) return chartContainer;

                const values = data.map(d => d.value);
                const minVal = Math.min(...values);
                const maxVal = Math.max(...values);
                const range = maxVal - minVal || 1;

                // SVG dimensions
                const width = 600; // coordinate space
                const height = 200;
                const padding = 20;

                // Create SVG
                const svgNs = "http://www.w3.org/2000/svg";
                const svg = document.createElementNS(svgNs, "svg");
                svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
                svg.style.width = '100%';
                svg.style.height = '100%';

                // Calculate points
                const points = data.map((d, i) => {
                    const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
                    const y = height - padding - ((d.value - minVal) / range) * (height - 2 * padding);
                    return { x: x, y: y };
                });

                // Path for area (closed loop)
                let dArea = `M ${points[0].x} ${height - padding} L ${points[0].x} ${points[0].y}`;
                points.forEach(p => dArea += ` L ${p.x} ${p.y}`);
                dArea += ` L ${points[points.length - 1].x} ${height - padding} Z`;

                // Path for line (stroke)
                let dLine = `M ${points[0].x} ${points[0].y}`;
                points.forEach(p => dLine += ` L ${p.x} ${p.y}`);

                // Area Path
                const areaPath = document.createElementNS(svgNs, "path");
                areaPath.setAttribute("d", dArea);
                areaPath.setAttribute("fill", `${comp.Chart.color}33`); // add transparency
                areaPath.setAttribute("stroke", "none");
                svg.appendChild(areaPath);

                // Line Path
                const linePath = document.createElementNS(svgNs, "path");
                linePath.setAttribute("d", dLine);
                linePath.setAttribute("fill", "none");
                linePath.setAttribute("stroke", comp.Chart.color);
                linePath.setAttribute("stroke-width", "2");
                svg.appendChild(linePath);

                // optional: add simple axis line
                const axisPath = document.createElementNS(svgNs, "path");
                axisPath.setAttribute("d", `M ${padding} ${height - padding} L ${width - padding} ${height - padding}`);
                axisPath.setAttribute("stroke", "#ccc");
                axisPath.setAttribute("stroke-width", "1");
                svg.appendChild(axisPath);

                chartContainer.appendChild(svg);
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
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Client-A2UI': isUiMode ? 'true' : 'false'
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (data.kind === 'a2ui') {
            addA2UIWidget(data.data);
        } else {
            addMessage(data.text || 'No response text', false);
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
