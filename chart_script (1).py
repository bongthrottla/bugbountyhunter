import plotly.graph_objects as go
import plotly.express as px
import json

# Complete timeline data with interpolated missing months
timeline_data = [
    {"month": 1, "phase": "Learning Foundation", "earnings_min": 0, "earnings_max": 50, "skills": "Setup & Basics", "key_activity": "Tool Install"},
    {"month": 2, "phase": "Learning Foundation", "earnings_min": 0, "earnings_max": 100, "skills": "Manual Testing", "key_activity": "First Recon"},
    {"month": 3, "phase": "Learning Foundation", "earnings_min": 50, "earnings_max": 200, "skills": "Vuln Finding", "key_activity": "First Bug Sub"},
    {"month": 4, "phase": "Building Reputation", "earnings_min": 200, "earnings_max": 500, "skills": "Efficient Hunt", "key_activity": "Consistent Sub"},
    {"month": 5, "phase": "Building Reputation", "earnings_min": 300, "earnings_max": 800, "skills": "Advanced Meth", "key_activity": "Private Apps"},
    {"month": 6, "phase": "Building Reputation", "earnings_min": 500, "earnings_max": 1200, "skills": "Specialization", "key_activity": "Custom Tools"},
    {"month": 7, "phase": "Building Reputation", "earnings_min": 600, "earnings_max": 1400, "skills": "Advanced Hunt", "key_activity": "Complex Bugs"},
    {"month": 8, "phase": "Building Reputation", "earnings_min": 700, "earnings_max": 1600, "skills": "Expertise", "key_activity": "Research"},
    {"month": 9, "phase": "Scaling Up", "earnings_min": 1000, "earnings_max": 3000, "skills": "Expert Level", "key_activity": "Private Progs"},
    {"month": 10, "phase": "Scaling Up", "earnings_min": 1200, "earnings_max": 3500, "skills": "Advanced Exp", "key_activity": "Complex Hunt"},
    {"month": 11, "phase": "Scaling Up", "earnings_min": 1500, "earnings_max": 4000, "skills": "Thought Lead", "key_activity": "Conferences"},
    {"month": 12, "phase": "Scaling Up", "earnings_min": 2000, "earnings_max": 5000, "skills": "Community Lead", "key_activity": "Teaching"}
]

# Calculate midpoints and error bars
months = [item["month"] for item in timeline_data]
earnings_mid = [(item["earnings_min"] + item["earnings_max"]) / 2 for item in timeline_data]
earnings_min = [item["earnings_min"] for item in timeline_data]
earnings_max = [item["earnings_max"] for item in timeline_data]
skills = [item["skills"] for item in timeline_data]
activities = [item["key_activity"] for item in timeline_data]
phases = [item["phase"] for item in timeline_data]

# Create the figure
fig = go.Figure()

# Add earnings progression with error bars showing ranges
fig.add_trace(go.Scatter(
    x=months,
    y=earnings_mid,
    mode='markers+lines',
    name='Earnings Range',
    marker=dict(size=10, color='#1FB8CD'),
    line=dict(width=3, color='#1FB8CD'),
    error_y=dict(
        type='data',
        symmetric=False,
        array=[max_val - mid_val for max_val, mid_val in zip(earnings_max, earnings_mid)],
        arrayminus=[mid_val - min_val for mid_val, min_val in zip(earnings_mid, earnings_min)],
        visible=True,
        color='#1FB8CD',
        thickness=2
    ),
    hovertemplate='<b>Month %{x}</b><br>' +
                 'Earnings: $%{customdata[0]}-$%{customdata[1]}<br>' +
                 'Phase: %{customdata[2]}<br>' +
                 'Skills: %{customdata[3]}<br>' +
                 'Focus: %{customdata[4]}<extra></extra>',
    customdata=list(zip(earnings_min, earnings_max, phases, skills, activities))
))

# Add phase background colors
phase_colors = {"Learning Foundation": "#B3E5EC", "Building Reputation": "#FFCDD2", "Scaling Up": "#A5D6A7"}
current_phase = None
phase_start = 1

for i, phase in enumerate(phases + [None]):  # Add None to trigger final phase
    if phase != current_phase:
        if current_phase is not None:
            # Add background rectangle for previous phase
            fig.add_shape(
                type="rect",
                x0=phase_start - 0.5,
                x1=months[i-1] + 0.5,
                y0=0,
                y1=max(earnings_max) * 1.1,
                fillcolor=phase_colors.get(current_phase, "#F0F0F0"),
                opacity=0.2,
                layer="below",
                line_width=0
            )
        current_phase = phase
        phase_start = months[i] if i < len(months) else months[-1]

# Update layout
fig.update_layout(
    title="Bug Bounty Earnings: 12-Month Journey",
    xaxis_title="Month",
    yaxis_title="Earnings ($)",
    showlegend=False
)

# Update axes
fig.update_xaxes(
    tickvals=list(range(1, 13)), 
    ticktext=[f"M{i}" for i in range(1, 13)],
    range=[0.5, 12.5]
)
fig.update_yaxes(
    tickformat='$,.0f',
    range=[0, max(earnings_max) * 1.1]
)

# Update traces for better visibility
fig.update_traces(cliponaxis=False)

# Save the chart
fig.write_image("bug_bounty_roadmap.png")
fig.write_image("bug_bounty_roadmap.svg", format="svg")
print("Chart saved as bug_bounty_roadmap.png and bug_bounty_roadmap.svg")