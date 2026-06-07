import json
from collections import defaultdict
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import html as html_mod
import plotly.graph_objects as go

st.set_page_config(page_title="Homework1 SET50 Social Network", layout="wide")

with st.sidebar:
    st.markdown("# Homework1")

st.title("SET50 Social Network")

df = pd.read_csv("SET50_Companies_and_Stakeholders.csv")

SHAREHOLDER_COLS = [
    ("Stakeholder 1", "Share % 1"),
    ("Stakeholder 2", "Share % 2"),
    ("Stakeholder 3", "Share % 3"),
    ("Stakeholder 4", "Share % 4"),
    ("Stakeholder 5", "Share % 5"),
]


def build_graph_data(df):
    companies = {}
    stakeholders = {}
    edges = []

    for _, row in df.iterrows():
        symbol = str(row["Symbol"]).strip()
        company_name = str(row["Company Name (EN)"]).strip()
        cid = f"c_{symbol}"
        companies[cid] = {"label": symbol, "_name": company_name}

        for s_col, p_col in SHAREHOLDER_COLS:
            s_val = row[s_col]
            p_val = row[p_col]
            if pd.isna(s_val) or pd.isna(p_val):
                continue
            s_name = str(s_val).strip()
            sid = f"s_{s_name}"
            stakeholders[sid] = {"label": s_name, "_name": s_name}
            edges.append({
                "from": cid,
                "to": sid,
                "share_pct": float(p_val),
            })

    company_conn = {}
    stakeholder_conn = {}
    for e in edges:
        company_conn[e["from"]] = company_conn.get(e["from"], 0) + 1
        stakeholder_conn[e["to"]] = stakeholder_conn.get(e["to"], 0) + 1

    for cid, c in companies.items():
        c["title"] = (
            f"Symbol: {html_mod.escape(c['label'])}<br>"
            f"Company Name: {html_mod.escape(c['_name'])}<br>"
            f"Connected Stakeholders: {company_conn.get(cid, 0)}"
        )
        del c["_name"]

    for sid, s in stakeholders.items():
        s["title"] = (
            f"Stakeholder: {html_mod.escape(s['label'])}<br>"
            f"Connected Companies: {stakeholder_conn.get(sid, 0)}"
        )
        del s["_name"]

    company_map = {cid: c["label"] for cid, c in companies.items()}
    stakeholder_map = {sid: s["label"] for sid, s in stakeholders.items()}
    for e in edges:
        e["title"] = (
            f"Company: {html_mod.escape(company_map[e['from']])}<br>"
            f"Stakeholder: {html_mod.escape(stakeholder_map[e['to']])}<br>"
            f"Shareholding: {e['share_pct']:.2f}%"
        )

    return companies, stakeholders, edges


all_companies, all_stakeholders, all_edges = build_graph_data(df)

num_nodes = len(all_companies) + len(all_stakeholders)
num_edges = len(all_edges)

adj = defaultdict(set)
for e in all_edges:
    adj[e["from"]].add(e["to"])
    adj[e["to"]].add(e["from"])

visited = set()
num_components = 0
for node in adj:
    if node not in visited:
        num_components += 1
        stack = [node]
        while stack:
            n = stack.pop()
            if n not in visited:
                visited.add(n)
                for nb in adj[n]:
                    if nb not in visited:
                        stack.append(nb)

total_degree = sum(len(nb) for nb in adj.values())
avg_degree = total_degree / num_nodes if num_nodes > 0 else 0
density = (2 * num_edges) / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0.0

stakeholder_degree = defaultdict(int)
for e in all_edges:
    stakeholder_degree[e["to"]] += 1

st.header("Search Panel")
all_symbols = sorted(df["Symbol"].unique().tolist())

all_stakeholder_names = sorted(set(
    str(name).strip()
    for s_col, _ in SHAREHOLDER_COLS
    for name in df[s_col].dropna()
))

col1, col2 = st.columns(2)
with col1:
    selected_company = st.selectbox(
        "Search Company",
        all_symbols,
        index=None,
        placeholder="Type company symbol...",
        key="company_select"
    )
with col2:
    selected_stakeholder = st.selectbox(
        "Search Stakeholder",
        all_stakeholder_names,
        index=None,
        placeholder="Type stakeholder name...",
        key="stakeholder_select"
    )


def build_selected_ids(company, stakeholder):
    ids = []
    if company:
        ids.append(f"c_{company}")
    if stakeholder:
        ids.append(f"s_{stakeholder}")
    return ids


selected_ids = build_selected_ids(selected_company, selected_stakeholder)
selected_ids_json = json.dumps(selected_ids)


def js_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")


def generate_network_html(companies, stakeholders, edges, selected_ids):
    nodes_parts = []
    for cid, c in companies.items():
        nodes_parts.append(
            f'{{id:"{js_str(cid)}",label:"{js_str(c["label"])}",'
            f'title:"{js_str(c["title"])}",shape:"box",color:"#A8D5BA",'
            f'borderWidth:1,borderWidthSelected:2,size:25,'
            f'font:{{size:13,face:"Arial",color:"#5D3B52"}},'
            f'color:{{background:"#A8D5BA",border:"#E8A8C8",highlight:{{background:"#8EC4A0",border:"#6B9B7A"}},'
            f'hover:{{background:"#A8D5BA",border:"#6B9B7A"}}}}}}'
        )

    for sid, s in stakeholders.items():
        nodes_parts.append(
            f'{{id:"{js_str(sid)}",label:"{js_str(s["label"])}",'
            f'title:"{js_str(s["title"])}",shape:"dot",color:"#DCC6F0",'
            f'borderWidth:1,borderWidthSelected:2,size:20,'
            f'font:{{size:13,face:"Arial",color:"#5D3B52"}},'
            f'color:{{border:"#E8A8C8",highlight:{{background:"#CE93D8",border:"#AB47BC"}},'
            f'hover:{{background:"#DCC6F0",border:"#AB47BC"}}}}}}'
        )

    edges_parts = []
    for e in edges:
        pct = e["share_pct"]
        width = max(0.5, pct / 5)
        edges_parts.append(
            f'{{from:"{js_str(e["from"])}",to:"{js_str(e["to"])}",'
            f'title:"{js_str(e["title"])}",'
            f'color:"#E8A8C8",width:{width:.1f},smooth:false,'
            f'font:{{size:10,color:"#8B5B7A",strokeWidth:2,strokeColor:"#FFF7FB"}},'
            f'color:{{color:"#E8A8C8",highlight:"#D48BA8",hover:"#D48BA8"}}}}'
        )

    nodes_str = ",\n".join(nodes_parts) if nodes_parts else ""
    edges_str = ",\n".join(edges_parts) if edges_parts else ""
    status = f"{len(companies)} companies  ·  {len(stakeholders)} stakeholders  ·  {len(edges)} connections"

    template = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#FFF7FB;font-family:-apple-system,BlinkMacSystemFont,sans-serif;overflow:hidden}
#mynetwork{width:100%;height:750px;background:#FFF7FB}
.ctrl{position:absolute;top:12px;right:12px;z-index:999;display:flex;flex-direction:column;gap:4px}
.ctrl button{width:36px;height:32px;cursor:pointer;border:1px solid #E8A8C8;background:#FFF7FB;color:#8B5B7A;
font-size:15px;font-weight:bold;border-radius:4px;display:flex;align-items:center;justify-content:center;
transition:all 0.12s;line-height:1;padding:0}
.ctrl button:hover{background:#F8BBD0;border-color:#D48BA8;color:#5D3B52}
.leg{position:absolute;bottom:12px;left:12px;z-index:999;background:#FFF7FB;border:1px solid #E8A8C8;border-radius:6px;padding:8px 12px;font-size:11px;color:#8B5B7A;line-height:1.8}
.leg-t{font-weight:bold;font-size:12px;margin-bottom:2px}
.leg-s{display:inline-block;height:3px;border-radius:2px;vertical-align:middle;margin-right:6px;background:#E8A8C8}
.leg-s1{width:20px;height:1px}
.leg-s2{width:20px;height:4px}
.leg-s3{width:20px;height:8px}
.st{text-align:center;padding:5px;color:#8B5B7A;font-size:12px;background:#FFF7FB;border-top:1px solid #F8BBD0}
.wrap{position:relative;width:100%}
</style>
</head>
<body>
<div class="wrap">
<div class="ctrl">
<button onclick="zi()" title="Zoom In">+</button>
<button onclick="zo()" title="Zoom Out">−</button>
<button onclick="rv()" title="Reset View">⟲</button>
<button onclick="fn()" title="Fit Network">⊞</button>
<div id="mynetwork"></div>
<div class="st" id="st">__STATUS__</div>
</div>
<script>
var nodes=new vis.DataSet([__NODES__]);
var edges=new vis.DataSet([__EDGES__]);
var c=document.getElementById('mynetwork');
var data={nodes:nodes,edges:edges};
var allNodeIds=nodes.getIds();
var allEdgeIds=edges.getIds();
var origEdge={};
allEdgeIds.forEach(function(eid){var ed=edges.get(eid);origEdge[eid]={width:ed.width,color:JSON.parse(JSON.stringify(ed.color))};});
var options={
physics:{
solver:'barnesHut',
barnesHut:{
gravitationalConstant:-5000,
centralGravity:0.3,
springLength:300,
springConstant:0.02,
damping:0.09
},
stabilization:{iterations:1000,fit:false}
},
layout:{improvedLayout:true,randomSeed:42},
edges:{
smooth:false,
font:{size:10,color:'#8B5B7A',strokeWidth:2,strokeColor:'#FFF7FB'},
color:{color:'#E8A8C8',highlight:'#D48BA8',hover:'#D48BA8'},
hoverWidth:2
},
nodes:{
font:{face:'Arial',color:'#5D3B52'},
borderWidth:1,
borderWidthSelected:2,
color:{
border:'#E8A8C8',
highlight:{background:'#F48FB1',border:'#D48BA8'},
hover:{background:'#F8BBD0',border:'#D48BA8'}
}
},
interaction:{
hover:true,
tooltipDelay:100,
tooltipStyle:'html',
navigationButtons:false,
keyboard:false,
selectable:true,
selectConnectedEdges:true
},
configure:{filter:function(o,p){return false;}}
};
var net=new vis.Network(c,data,options);
var selectedIds=__SELECTED_IDS__;

function applyHighlight(ids){
if(!ids||ids.length===0){
allNodeIds.forEach(function(nid){
var isCompany=nid.indexOf('c_')===0;
nodes.update({id:nid,color:{background:isCompany?'#A8D5BA':'#DCC6F0',border:'#E8A8C8'},font:{color:'#5D3B52',size:13}});
});
allEdgeIds.forEach(function(eid){
var o=origEdge[eid];edges.update({id:eid,color:o.color,width:o.width});
});
net.fit({animation:true});
return;
}
var hiliteNodes=new Set(ids);
var hiliteEdges=new Set();
ids.forEach(function(sid){
var ce=net.getConnectedEdges(sid);
ce.forEach(function(eid){hiliteEdges.add(eid);});
var cn=net.getConnectedNodes(sid);
cn.forEach(function(nid){hiliteNodes.add(nid);});
});
allNodeIds.forEach(function(nid){
if(hiliteNodes.has(nid)){
var isCompany=nid.indexOf('c_')===0;
var isSelected=ids.indexOf(nid)!==-1;
nodes.update({id:nid,color:{background:isCompany?'#A8D5BA':'#DCC6F0',border:isSelected?'#FF6B8A':'#E8A8C8'},font:{color:'#5D3B52',size:isSelected?15:13}});
}else{
nodes.update({id:nid,color:{background:'#F0EBF0',border:'#E0D6E0'},font:{color:'#C8BCC8',size:11}});
}
});
allEdgeIds.forEach(function(eid){
if(hiliteEdges.has(eid)){
var o=origEdge[eid];edges.update({id:eid,color:o.color,width:o.width});
}else{
edges.update({id:eid,color:{color:'#F0E4EC',highlight:'#F0E4EC',hover:'#F0E4EC'},width:0.3});
}
});
if(ids.length===1){net.focus(ids[0],{scale:1.5,animation:true});}
else{net.fit({animation:true});}
}

applyHighlight(selectedIds);

function zi(){net.zoomIn(0.2);}
function zo(){net.zoomOut(0.2);}
function rv(){net.moveTo({scale:1.0,position:{x:0,y:0}});}
function fn(){net.fit({animation:true});}
</script>
</body>
</html>"""

    return template.replace("__NODES__", nodes_str).replace("__EDGES__", edges_str).replace("__STATUS__", status).replace("__SELECTED_IDS__", selected_ids)


html = generate_network_html(all_companies, all_stakeholders, all_edges, selected_ids_json)

st.header("Network Statistics")
st.markdown(f"""
<style>
.sc {{background:#FFF7FB;border:1px solid #E8A8C8;border-radius:8px;padding:14px 8px;text-align:center;height:100%}}
.sc-l {{font-size:11px;color:#8B5B7A;margin-bottom:4px}}
.sc-v {{font-size:22px;font-weight:bold;color:#5D3B52}}
</style>
<div style="display:flex;gap:12px;margin-bottom:8px">
<div style="flex:1"><div class="sc"><div class="sc-l">Nodes</div><div class="sc-v">{num_nodes}</div></div></div>
<div style="flex:1"><div class="sc"><div class="sc-l">Edges</div><div class="sc-v">{num_edges}</div></div></div>
<div style="flex:1"><div class="sc"><div class="sc-l">Avg Degree</div><div class="sc-v">{avg_degree:.2f}</div></div></div>
<div style="flex:1"><div class="sc"><div class="sc-l">Density</div><div class="sc-v">{density:.4f}</div></div></div>
<div style="flex:1"><div class="sc"><div class="sc-l">Components</div><div class="sc-v">{num_components}</div></div></div>
</div>
""", unsafe_allow_html=True)

st.header("Network Visualization")
components.html(html, height=780, scrolling=False)

st.header("Top 10 Stakeholders by Degree Centrality")
top_10 = sorted(stakeholder_degree.items(), key=lambda x: x[1])
top_10 = top_10[-10:]
top_labels = [all_stakeholders[sid]["label"] for sid, _ in top_10]
top_values = [deg for _, deg in top_10]

fig = go.Figure(go.Bar(
    x=top_values,
    y=top_labels,
    orientation="h",
    marker_color="#A8D5BA",
    marker_line_color="#8EC4A0",
    marker_line_width=1,
    text=top_values,
    textposition="outside",
    textfont=dict(color="#5D3B52", size=12),
    hovertemplate="%{y}<br>Connected Companies (Degree): %{x}<extra></extra>",
))
fig.update_layout(
    height=400,
    margin=dict(l=0, r=50, t=8, b=0),
    paper_bgcolor="#FFF7FB",
    plot_bgcolor="#FFF7FB",
    font_color="#5D3B52",
    font_size=12,
    xaxis=dict(title="Degree (Connected Companies)", gridcolor="#F0E8EC", title_font_size=12),
    yaxis=dict(autorange="reversed", title=None),
    bargap=0.25,
)
fig.update_traces(
    marker=dict(cornerradius=4),
)
st.plotly_chart(fig, use_container_width=True)
