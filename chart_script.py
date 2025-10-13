import plotly.graph_objects as go
import networkx as nx

# Define nodes with their types for color mapping
nodes = [
    # GUI
    ('Main GUI', 'gui'),
    ('Scanner Tab', 'gui'),
    ('Program Guide Tab', 'gui'),
    ('Tools Tab', 'gui'),
    ('Reports Tab', 'gui'),
    ('Target Input', 'gui'),
    ('Scan Select', 'gui'),
    ('Progress Track', 'gui'),
    ('Output Disp', 'gui'),
    # Workflow/Scan Types
    ('Basic Recon', 'workflow'),
    ('Comprehen.', 'workflow'),
    ('XSS Hunt', 'workflow'),
    ('Dir Fuzz', 'workflow'),
    ('SQLi Disc.', 'workflow'),
    # Tool Integration
    ('Tool Integr.', 'tools'),
    ('Subfinder', 'tools'),
    ('httpx', 'tools'),
    ('Nuclei', 'tools'),
    ('ffuf', 'tools'),
    ('Dalfox', 'tools'),
    ('SQLMap', 'tools'),
    # Backend
    ('DB Layer', 'backend'),
    ('SQLite', 'backend'),
    ('Scan Hist.', 'backend'),
    ('Subd Track', 'backend'),
    ('Vuln Store', 'backend'),
    # Output
    ('Report Gen.', 'output'),
    ('Markdown', 'output'),
    ('Exec Sum.', 'output'),
    ('Tech Det.', 'output'),
    ('Vuln Rep.', 'output')
]

node_ids = [n[0] for n in nodes]
node_types = {n[0]:n[1] for n in nodes}
color_map = {
    'gui': '#B3E5EC',
    'workflow': '#A5D6A7',
    'tools': '#FFEB8A',
    'backend': '#FFCDD2',
    'output': '#9FA8B0',
}
node_colors = [color_map[node_types[n]] for n in node_ids]

# Define edge arrows to direct flow
edges = [
    # GUI
    ('Main GUI', 'Scanner Tab'),
    ('Main GUI', 'Program Guide Tab'),
    ('Main GUI', 'Tools Tab'),
    ('Main GUI', 'Reports Tab'),
    ('Scanner Tab', 'Target Input'),
    ('Scanner Tab', 'Scan Select'),
    ('Scanner Tab', 'Progress Track'),
    ('Scanner Tab', 'Output Disp'),
    # Scan Select to Scan Types
    ('Scan Select', 'Basic Recon'),
    ('Scan Select', 'Comprehen.'),
    ('Scan Select', 'XSS Hunt'),
    ('Scan Select', 'Dir Fuzz'),
    ('Scan Select', 'SQLi Disc.'),
    # Types to Tool Integration
    ('Basic Recon', 'Tool Integr.'),
    ('Comprehen.', 'Tool Integr.'),
    ('XSS Hunt', 'Tool Integr.'),
    ('Dir Fuzz', 'Tool Integr.'),
    ('SQLi Disc.', 'Tool Integr.'),
    # Tool Integration tools
    ('Tool Integr.', 'Subfinder'),
    ('Tool Integr.', 'httpx'),
    ('Tool Integr.', 'Nuclei'),
    ('Tool Integr.', 'ffuf'),
    ('Tool Integr.', 'Dalfox'),
    ('Tool Integr.', 'SQLMap'),
    # Tools to DB
    ('Subfinder', 'DB Layer'),
    ('httpx', 'DB Layer'),
    ('Nuclei', 'DB Layer'),
    ('ffuf', 'DB Layer'),
    ('Dalfox', 'DB Layer'),
    ('SQLMap', 'DB Layer'),
    # DB Layer functions
    ('DB Layer', 'SQLite'),
    ('DB Layer', 'Scan Hist.'),
    ('DB Layer', 'Subd Track'),
    ('DB Layer', 'Vuln Store'),
    # DB Layer to Output
    ('DB Layer', 'Report Gen.'),
    ('Output Disp', 'Report Gen.'),
    ('Reports Tab', 'Report Gen.'),
    # Report Generator to Outputs
    ('Report Gen.', 'Markdown'),
    ('Report Gen.', 'Exec Sum.'),
    ('Report Gen.', 'Tech Det.'),
    ('Report Gen.', 'Vuln Rep.')
]

G = nx.DiGraph()
for n in node_ids:
    G.add_node(n)
G.add_edges_from(edges)

# Arrange nodes in a hierarchical top-down layout manually
# levels: 0-GUI Main, 1-Tabs, 2-GUI Functions, 3-Scan Types, 4-Tool Integration, 5-Tools, 6-DB, 7-DB Func, 8-Output
x_dict = {}
y_dict = {}
layout = {
    0: ('Main GUI',),
    1: ('Scanner Tab','Program Guide Tab','Tools Tab','Reports Tab'),
    2: ('Target Input','Scan Select','Progress Track','Output Disp'),
    3: ('Basic Recon','Comprehen.','XSS Hunt','Dir Fuzz','SQLi Disc.'),
    4: ('Tool Integr.',),
    5: ('Subfinder','httpx','Nuclei','ffuf','Dalfox','SQLMap'),
    6: ('DB Layer',),
    7: ('SQLite','Scan Hist.','Subd Track','Vuln Store'),
    8: ('Report Gen.',),
    9: ('Markdown','Exec Sum.','Tech Det.','Vuln Rep.')
}
for yi, layer in layout.items():
    for xi, node in enumerate(layer):
        x = -1 + (2*xi/(max(1,len(layer)-1))) if len(layer)>1 else 0
        x_dict[node]=x
        y_dict[node]= -yi

node_x = [x_dict[n] for n in node_ids]
node_y = [y_dict[n] for n in node_ids]

# Edge traces for arrows
edge_x = []
edge_y = []
edge_shapes = []
for a, b in G.edges():
    x0, y0 = x_dict[a], y_dict[a]
    x1, y1 = x_dict[b], y_dict[b]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]
    # Arrow annotation
    edge_shapes.append(dict(
        type="path",
        path=f"M{x0},{y0} L{x1},{y1}",
        layer="above",
        line=dict(color="#888", width=1),
        arrowhead=2
    ))

fig = go.Figure()
# Draw edge lines
fig.add_trace(go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=1, color='#666'),
    hoverinfo='none',
    mode='lines',
    showlegend=False
))
# Draw nodes
fig.add_trace(go.Scatter(
    x=node_x,
    y=node_y,
    mode='markers+text',
    marker=dict(
        size=36,
        color=node_colors,
        line=dict(width=2, color='#333')
    ),
    text=node_ids,
    textfont=dict(size=10, color='#13343B'),
    textposition="middle center",
    hovertemplate='<b>%{text}</b><extra></extra>',
    showlegend=False
))

fig.update_layout(
    title='BugBountyHunter Architecture',
    showlegend=False,
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor='white'
)

fig.write_image("bugbounty_architecture.png")
fig.write_image("bugbounty_architecture.svg", format="svg")