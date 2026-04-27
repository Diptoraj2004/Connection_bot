// components/AdminDashboard/HeatmapPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Plotly from 'plotly.js-dist-min';
import './HeatmapPage.css';

const HeatmapPage = () => {
  const navigate = useNavigate();
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [loading, setLoading] = useState(false);

  // Sample Student Dataset (same as your Python code)
  const data = [
    { StudentID: 1, Department: "CS", StressLevel: 4, Anxiety: 3, Depression: 2 },
    { StudentID: 2, Department: "EE", StressLevel: 2, Anxiety: 1, Depression: 1 },
    { StudentID: 3, Department: "CS", StressLevel: 5, Anxiety: 4, Depression: 4 },
    { StudentID: 4, Department: "ME", StressLevel: 3, Anxiety: 2, Depression: 2 },
    { StudentID: 5, Department: "EE", StressLevel: 1, Anxiety: 2, Depression: 1 },
    { StudentID: 6, Department: "ME", StressLevel: 4, Anxiety: 3, Depression: 3 },
    { StudentID: 7, Department: "CS", StressLevel: 3, Anxiety: 3, Depression: 3 },
    { StudentID: 8, Department: "EE", StressLevel: 2, Anxiety: 2, Depression: 1 },
    { StudentID: 9, Department: "ME", StressLevel: 5, Anxiety: 4, Depression: 5 },
    { StudentID: 10, Department: "CS", StressLevel: 4, Anxiety: 4, Depression: 3 }
  ];

  // Group by Department and calculate means
  const groupByDepartment = (data) => {
    const departments = [...new Set(data.map(item => item.Department))];
    const metrics = ['StressLevel', 'Anxiety', 'Depression'];
    
    const grouped = {};
    departments.forEach(dept => {
      grouped[dept] = {};
      metrics.forEach(metric => {
        const deptData = data.filter(item => item.Department === dept);
        const avg = deptData.reduce((sum, item) => sum + item[metric], 0) / deptData.length;
        grouped[dept][metric] = Math.round(avg * 10) / 10;
      });
    });
    return grouped;
  };

  const generateHeatmap = async () => {
    setLoading(true);
    
    // Simulate loading time
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const groupedData = groupByDepartment(data);
    const departments = Object.keys(groupedData);
    const metrics = ['StressLevel', 'Anxiety', 'Depression'];

    // Prepare data for heatmap
    const z = metrics.map(metric => 
      departments.map(dept => groupedData[dept][metric])
    );

    const heatmapData = [{
      z: z,
      x: departments,
      y: metrics,
      type: 'heatmap',
      colorscale: [
        [0, '#3182bd'],    // Cool (low values)
        [0.5, '#ffffff'],  // White (medium)
        [1, '#de2d26']     // Warm (high values)
      ],
      showscale: true,
      hoverongaps: false,
      texttemplate: "%{z}",
      textfont: { size: 14, color: "black" }
    }];

    const layout = {
      title: {
        text: 'Average Mental Health Indicators by Department',
        font: { size: 20, family: 'Inter, sans-serif', color: '#1f2937' }
      },
      xaxis: {
        title: 'Departments',
        tickfont: { size: 14 },
        titlefont: { size: 16 }
      },
      yaxis: {
        title: 'Mental Health Indicators',
        tickfont: { size: 14 },
        titlefont: { size: 16 }
      },
      width: 900,
      height: 600,
      margin: { l: 120, r: 50, t: 100, b: 80 },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)'
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
      displaylogo: false
    };

    Plotly.newPlot('heatmap-container', heatmapData, layout, config);
    setShowHeatmap(true);
    setLoading(false);
  };

  useEffect(() => {
    generateHeatmap();
  }, []);

  return (
    <div className="heatmap-page">
      {/* Header */}
      <header className="heatmap-header">
        <div className="header-content">
          <button className="back-btn" onClick={() => navigate('/admin')}>
            ← Back to Dashboard
          </button>
          <div className="header-info">
            <h1>Mental Health Heatmap Analysis</h1>
            <p>Department-wise visualization of student mental health indicators</p>
          </div>
          <div className="header-actions">
            <button className="refresh-btn" onClick={generateHeatmap}>
              🔄 Refresh Data
            </button>
            <button className="export-btn">
              📊 Export Chart
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="heatmap-main">
        <div className="heatmap-container-wrapper">
          {loading && (
            <div className="loading-overlay">
              <div className="loading-spinner"></div>
              <p>Generating heatmap...</p>
            </div>
          )}
          
          <div className="heatmap-card">
            <div id="heatmap-container"></div>
          </div>
          
          {showHeatmap && (
            <div className="insights-section">
              <h3>Key Insights</h3>
              <div className="insights-grid">
                <div className="insight-card">
                  <h4>🎯 Highest Risk</h4>
                  <p>Mechanical Engineering shows highest stress levels</p>
                </div>
                <div className="insight-card">
                  <h4>✅ Best Performance</h4>
                  <p>Electrical Engineering has lowest anxiety scores</p>
                </div>
                <div className="insight-card">
                  <h4>📊 Overall Trend</h4>
                  <p>Stress levels correlate with academic workload</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default HeatmapPage;
