const chartElement = document.getElementById("graphChart");
const nodeInfo = document.getElementById("nodeInfo");
const searchForm = document.getElementById("graphSearch");
const chart = echarts.init(chartElement);

const colors = {
  "课程": "#25636f",
  "知识点": "#b45732",
  "中图法": "#5d6b2f",
  "文化": "#7b4c9f",
  "机构": "#9b6a20",
  "个人": "#2f6f46",
  "计算": "#3d5f9f",
  "Course": "#25636f",
  "KnowledgePoint": "#b45732",
  "CLCClass": "#5d6b2f",
  "DimensionValue": "#3d5f9f"
};

async function loadGraph(query = "") {
  const response = await fetch(`/api/graph?q=${encodeURIComponent(query)}`);
  const graph = await response.json();
  const categories = Array.from(new Set(graph.nodes.map((node) => node.category))).map((name) => ({ name }));

  chart.setOption({
    color: categories.map((item) => colors[item.name] || "#64748b"),
    tooltip: {
      formatter: (params) => {
        if (params.dataType === "edge") {
          return params.data.relation;
        }
        return `${params.data.name}<br>${params.data.category || ""}`;
      }
    },
    legend: {
      top: 8,
      data: categories.map((item) => item.name)
    },
    series: [
      {
        type: "graph",
        layout: "force",
        roam: true,
        draggable: true,
        categories,
        label: {
          show: true,
          fontSize: 12,
          color: "#172026"
        },
        edgeLabel: {
          show: true,
          formatter: (params) => params.data.relation,
          fontSize: 10,
          color: "#64748b"
        },
        force: {
          repulsion: 220,
          edgeLength: [70, 140],
          gravity: 0.08
        },
        lineStyle: {
          color: "#94a3b8",
          opacity: 0.78
        },
        data: graph.nodes.map((node) => ({
          ...node,
          category: node.category,
          symbolSize: node.symbolSize || 36
        })),
        links: graph.links
      }
    ]
  });
}

chart.on("click", (params) => {
  if (params.dataType !== "node") {
    return;
  }
  const data = params.data;
  nodeInfo.innerHTML = `
    <div class="item-title">${data.name}</div>
    <p>类型：${data.category || "-"}</p>
    ${data.code ? `<p>代码：${data.code}</p>` : ""}
  `;
});

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(searchForm);
  loadGraph(formData.get("q") || "");
});

window.addEventListener("resize", () => chart.resize());
loadGraph();

