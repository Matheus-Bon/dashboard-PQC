import pandas as pd
import json
from core.chart_figures import fig_cloud_latency, fig_local_latency

# Mock data
data = {
    'library': ['A', 'A', 'B', 'B'],
    'response_ms': [10, 12, 20, 22],
    'environment': ['AWS', 'GCP', 'Local', 'Local'],
    'environment_type': ['cloud', 'cloud', 'local', 'local']
}
df = pd.DataFrame(data)

fig_c = fig_cloud_latency(df)
fig_l = fig_local_latency(df)

print("--- CLOUD FIGURE LAYOUT ---")
print(json.dumps(fig_c.layout.to_plotly_json(), indent=2))
print("--- LOCAL FIGURE LAYOUT ---")
print(json.dumps(fig_l.layout.to_plotly_json(), indent=2))

print("--- CLOUD DATA (TRACES) ---")
for i, t in enumerate(fig_c.data):
    print(f"Trace {i}: y={t.y[0]}, x={t.x[0]}, name={t.name}")

print("--- LOCAL DATA (TRACES) ---")
for i, t in enumerate(fig_l.data):
    print(f"Trace {i}: y={t.y[0]}, x={t.x[0]}, name={t.name}")
