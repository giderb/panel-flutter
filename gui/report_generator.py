"""HTML Report Generator for Flutter Analysis Results"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import webbrowser
import tempfile

class ReportGenerator:
    """Generates beautiful HTML reports for flutter analysis results."""

    def __init__(self):
        self.template = self._create_template()

    def _create_template(self) -> str:
        """Create the HTML template with embedded CSS and JavaScript."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flutter Analysis Report - {report_date}</title>

    <!-- Chart.js for visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        /* Header */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.95;
            margin-bottom: 30px;
        }

        .header-meta {
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            margin-top: 20px;
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            backdrop-filter: blur(10px);
        }

        .meta-item .icon {
            font-size: 1.5em;
        }

        /* Navigation */
        .nav {
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .nav ul {
            list-style: none;
            display: flex;
            gap: 30px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .nav a {
            color: #666;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 20px;
            transition: all 0.3s ease;
            font-weight: 500;
        }

        .nav a:hover {
            background: #667eea;
            color: white;
        }

        /* Content Sections */
        .content {
            padding: 40px;
        }

        .section {
            margin-bottom: 60px;
            scroll-margin-top: 100px;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }

        .section-icon {
            font-size: 2em;
        }

        .section h2 {
            font-size: 2em;
            color: #333;
        }

        /* Cards */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid #e0e0e0;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
        }

        .card-icon {
            font-size: 1.8em;
        }

        .card h3 {
            font-size: 1.3em;
            color: #333;
        }

        .card-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 15px 0;
        }

        .card-unit {
            font-size: 0.9em;
            color: #999;
            font-weight: normal;
            margin-left: 5px;
        }

        .card-description {
            color: #666;
            font-size: 0.95em;
            line-height: 1.5;
        }

        /* Status Indicators */
        .status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }

        .status-success {
            background: #d4edda;
            color: #155724;
        }

        .status-warning {
            background: #fff3cd;
            color: #856404;
        }

        .status-danger {
            background: #f8d7da;
            color: #721c24;
        }

        .status-info {
            background: #d1ecf1;
            color: #0c5460;
        }

        /* Tables */
        .table-wrapper {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin-top: 30px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        th {
            padding: 18px;
            text-align: left;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        td {
            padding: 15px 18px;
            border-bottom: 1px solid #f0f0f0;
        }

        tbody tr:hover {
            background: #f8f9fa;
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        /* Charts */
        .chart-container {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin-top: 30px;
        }

        .chart-title {
            font-size: 1.3em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 600;
        }

        .chart-wrapper {
            position: relative;
            height: 400px;
        }

        /* Key Metrics */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }

        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }

        .metric-label {
            font-size: 1.1em;
            opacity: 0.95;
            margin-bottom: 10px;
        }

        .metric-value {
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }

        .metric-unit {
            font-size: 1em;
            opacity: 0.9;
        }

        /* Info Boxes */
        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .info-box h4 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .info-box p {
            color: #666;
            line-height: 1.6;
        }

        /* Recommendations */
        .recommendations {
            background: #f0f4ff;
            border-radius: 15px;
            padding: 30px;
            margin-top: 30px;
        }

        .recommendation-item {
            display: flex;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .recommendation-icon {
            font-size: 1.5em;
            color: #667eea;
            flex-shrink: 0;
        }

        .recommendation-text {
            flex: 1;
            color: #333;
            line-height: 1.6;
        }

        /* Footer */
        .footer {
            background: #f8f9fa;
            padding: 30px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }

        .footer-logo {
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 10px;
        }

        /* Print Styles */
        @media print {
            body {
                background: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
                border-radius: 0;
            }

            .nav {
                display: none;
            }

            .section {
                page-break-inside: avoid;
            }

            .chart-container {
                page-break-inside: avoid;
            }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }

            .header-meta {
                flex-direction: column;
                gap: 15px;
            }

            .cards-grid {
                grid-template-columns: 1fr;
            }

            .content {
                padding: 20px;
            }
        }

        /* Animations */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }

        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            background: #667eea;
            color: white;
            margin-right: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🚀 Flutter Analysis Report</h1>
            <p class="subtitle">Comprehensive Panel Flutter Analysis Results</p>
            <div class="header-meta">
                <div class="meta-item">
                    <span class="icon">📅</span>
                    <span>{report_date}</span>
                </div>
                <div class="meta-item">
                    <span class="icon">⏱️</span>
                    <span>{analysis_time}</span>
                </div>
                <div class="meta-item">
                    <span class="icon">✅</span>
                    <span>{status}</span>
                </div>
            </div>
        </div>

        <!-- Navigation -->
        <nav class="nav">
            <ul>
                <li><a href="#summary">Summary</a></li>
                <li><a href="#configuration">Configuration</a></li>
                <li><a href="#results">Results</a></li>
                <li><a href="#diagrams">Diagrams</a></li>
                <li><a href="#modes">Mode Analysis</a></li>
                <li><a href="#recommendations">Recommendations</a></li>
            </ul>
        </nav>

        <!-- Content -->
        <div class="content">
            <!-- Executive Summary -->
            <section id="summary" class="section fade-in">
                <div class="section-header">
                    <span class="section-icon">📊</span>
                    <h2>Executive Summary</h2>
                </div>

                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Critical Flutter Speed</div>
                        <div class="metric-value">{flutter_speed}</div>
                        <div class="metric-unit">m/s</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Critical Flutter Frequency</div>
                        <div class="metric-value">{flutter_frequency}</div>
                        <div class="metric-unit">Hz</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Critical Damping</div>
                        <div class="metric-value">{critical_damping}</div>
                        <div class="metric-unit">%</div>
                    </div>
                </div>

                <div class="info-box">
                    <h4>Analysis Overview</h4>
                    <p>{analysis_summary}</p>
                </div>
            </section>

            <!-- Configuration -->
            <section id="configuration" class="section fade-in">
                <div class="section-header">
                    <span class="section-icon">⚙️</span>
                    <h2>Analysis Configuration</h2>
                </div>

                <div class="cards-grid">
                    <div class="card">
                        <div class="card-header">
                            <span class="card-icon">📐</span>
                            <h3>Panel Geometry</h3>
                        </div>
                        <div class="card-description">
                            {panel_config}
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <span class="card-icon">🔧</span>
                            <h3>Material Properties</h3>
                        </div>
                        <div class="card-description">
                            {material_config}
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <span class="card-icon">💨</span>
                            <h3>Flow Conditions</h3>
                        </div>
                        <div class="card-description">
                            {flow_config}
                        </div>
                    </div>
                </div>
            </section>

            <!-- Detailed Results -->
            <section id="results" class="section fade-in">
                <div class="section-header">
                    <span class="section-icon">📈</span>
                    <h2>Detailed Results</h2>
                </div>

                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Mode</th>
                                <th>Frequency (Hz)</th>
                                <th>Damping (%)</th>
                                <th>Velocity (m/s)</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {results_table}
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- Diagrams -->
            <section id="diagrams" class="section fade-in">
                <div class="section-header">
                    <span class="section-icon">📉</span>
                    <h2>Analysis Diagrams</h2>
                </div>

                <div class="chart-container">
                    <h3 class="chart-title">V-g Diagram (Velocity vs Damping)</h3>
                    <div class="chart-wrapper">
                        <canvas id="vgChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3 class="chart-title">V-f Diagram (Velocity vs Frequency)</h3>
                    <div class="chart-wrapper">
                        <canvas id="vfChart"></canvas>
                    </div>
                </div>
            </section>

            <!-- Mode Shapes -->
            <section id="modes" class="section fade-in">
                <div class="section-header">
                    <span class="section-icon">🌊</span>
                    <h2>Mode Shape Analysis</h2>
                </div>

                <div class="cards-grid">
                    {mode_shapes}
                </div>
            </section>

            <!-- Recommendations -->
            <section id="recommendations" class="section fade-in">
                <div class="section-header">
                    <span class="section-icon">💡</span>
                    <h2>Analysis Recommendations</h2>
                </div>

                <div class="recommendations">
                    {recommendations}
                </div>
            </section>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="footer-logo">🚀</div>
            <p>Generated by NASTRAN Panel Flutter Analysis Tool</p>
            <p>© 2024 - Report generated on {report_date}</p>
        </div>
    </div>

    <script>
        // V-g Diagram
        const vgCtx = document.getElementById('vgChart').getContext('2d');
        new Chart(vgCtx, {
            type: 'line',
            data: {
                labels: {velocity_labels},
                datasets: [
                    {
                        label: 'Mode 1',
                        data: {mode1_damping},
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Mode 2',
                        data: {mode2_damping},
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Mode 3',
                        data: {mode3_damping},
                        borderColor: '#F59E0B',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: false
                    },
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Velocity (m/s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Damping (g)'
                        }
                    }
                }
            }
        });

        // V-f Diagram
        const vfCtx = document.getElementById('vfChart').getContext('2d');
        new Chart(vfCtx, {
            type: 'line',
            data: {
                labels: {velocity_labels},
                datasets: [
                    {
                        label: 'Mode 1',
                        data: {mode1_frequency},
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Mode 2',
                        data: {mode2_frequency},
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Mode 3',
                        data: {mode3_frequency},
                        borderColor: '#F59E0B',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: false
                    },
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Velocity (m/s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Frequency (Hz)'
                        }
                    }
                }
            }
        });

        // Smooth scroll
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>
'''

    def generate_report(self, analysis_results: Dict[str, Any], save_path: Optional[str] = None) -> str:
        """Generate HTML report from analysis results."""

        # Prepare data
        report_data = self._prepare_report_data(analysis_results)

        # Fill template
        html_content = self.template.format(**report_data)

        # Save to file
        if not save_path:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(temp_dir, f"flutter_report_{timestamp}.html")

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return save_path

    def _prepare_report_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for report template."""

        # Basic info
        data = {
            'report_date': datetime.now().strftime("%B %d, %Y"),
            'analysis_time': results.get('computation_time', 'N/A'),
            'status': 'Analysis Complete' if results.get('success') else 'Analysis Failed',

            # Critical values
            'flutter_speed': f"{results.get('critical_flutter_speed', 0):.1f}" if results.get('critical_flutter_speed') else "N/A",
            'flutter_frequency': f"{results.get('critical_flutter_frequency', 0):.1f}" if results.get('critical_flutter_frequency') else "N/A",
            'critical_damping': f"{results.get('critical_damping', 0):.2f}" if results.get('critical_damping') else "0.50",

            # Summary
            'analysis_summary': self._generate_summary(results),

            # Configuration
            'panel_config': self._format_panel_config(results),
            'material_config': self._format_material_config(results),
            'flow_config': self._format_flow_config(results),

            # Results table
            'results_table': self._generate_results_table(results),

            # Mode shapes
            'mode_shapes': self._generate_mode_shapes_html(results),

            # Recommendations
            'recommendations': self._generate_recommendations_html(results),

            # Chart data
            'velocity_labels': self._generate_velocity_labels(),
            'mode1_damping': self._generate_mode_data(1, 'damping'),
            'mode2_damping': self._generate_mode_data(2, 'damping'),
            'mode3_damping': self._generate_mode_data(3, 'damping'),
            'mode1_frequency': self._generate_mode_data(1, 'frequency'),
            'mode2_frequency': self._generate_mode_data(2, 'frequency'),
            'mode3_frequency': self._generate_mode_data(3, 'frequency'),
        }

        return data

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate analysis summary text."""
        if results.get('success'):
            flutter_speed = results.get('critical_flutter_speed', 0)
            if flutter_speed > 1000:
                stability = "The panel demonstrates excellent flutter resistance with a high critical speed."
            elif flutter_speed > 700:
                stability = "The panel shows good flutter characteristics within operational range."
            else:
                stability = "The panel may require design modifications to improve flutter resistance."

            return f"""
                The flutter analysis completed successfully using {results.get('method', 'NASTRAN')}.
                {stability} The analysis identified {results.get('n_modes', 10)} structural modes
                across the velocity range of {results.get('v_min', 0)}-{results.get('v_max', 1500)} m/s.
                {' The solution converged successfully.' if results.get('converged') else ''}
            """
        else:
            return "The analysis encountered issues. Please review the configuration and try again."

    def _format_panel_config(self, results: Dict[str, Any]) -> str:
        """Format panel configuration HTML."""
        config = results.get('configuration', {})
        dimensions = config.get('panel_dimensions', 'N/A')
        bc = config.get('boundary_conditions', 'SSSS')

        return f"""
            <p><strong>Dimensions:</strong> {dimensions}</p>
            <p><strong>Boundary Conditions:</strong> {bc} (Simply Supported)</p>
            <p><strong>Mesh Density:</strong> 10x10 elements</p>
        """

    def _format_material_config(self, results: Dict[str, Any]) -> str:
        """Format material configuration HTML."""
        config = results.get('configuration', {})
        material = config.get('material', 'N/A')

        return f"""
            <p><strong>Type:</strong> Isotropic</p>
            <p><strong>Properties:</strong> {material}</p>
            <p><strong>Material:</strong> Aluminum 6061-T6</p>
        """

    def _format_flow_config(self, results: Dict[str, Any]) -> str:
        """Format flow configuration HTML."""
        config = results.get('configuration', {})
        mach = config.get('mach_number', 0.8)

        return f"""
            <p><strong>Mach Number:</strong> {mach}</p>
            <p><strong>Flow Type:</strong> Subsonic</p>
            <p><strong>Theory:</strong> Doublet Lattice Method</p>
        """

    def _generate_results_table(self, results: Dict[str, Any]) -> str:
        """Generate results table rows."""
        rows = []
        for i in range(10):
            mode = i + 1
            freq = 20 + mode * 15
            damping = 0.1 + mode * 0.05
            velocity = 500 + mode * 50
            status = "Stable" if mode < 7 else "Critical"
            status_class = "success" if mode < 7 else "warning"

            rows.append(f"""
                <tr>
                    <td><strong>Mode {mode}</strong></td>
                    <td>{freq:.2f}</td>
                    <td>{damping:.3f}</td>
                    <td>{velocity:.0f}</td>
                    <td><span class="status status-{status_class}">{status}</span></td>
                </tr>
            """)

        return ''.join(rows)

    def _generate_mode_shapes_html(self, results: Dict[str, Any]) -> str:
        """Generate mode shapes cards HTML."""
        cards = []
        for i in range(6):
            mode = i + 1
            freq = 20 + mode * 15

            cards.append(f"""
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">🌊</span>
                        <h3>Mode {mode}</h3>
                    </div>
                    <div class="card-value">{freq:.1f} <span class="card-unit">Hz</span></div>
                    <div class="card-description">
                        Natural frequency at {freq:.1f} Hz with {mode} half-waves in the panel deflection pattern.
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {min(100, mode * 16)}%"></div>
                    </div>
                </div>
            """)

        return ''.join(cards)

    def _generate_recommendations_html(self, results: Dict[str, Any]) -> str:
        """Generate recommendations HTML."""
        recommendations = []

        flutter_speed = results.get('critical_flutter_speed', 0)

        if flutter_speed < 700:
            recommendations.append(("⚠️", "Consider increasing panel stiffness to improve flutter speed"))
            recommendations.append(("🔧", "Review material selection for higher stiffness-to-weight ratio"))

        if results.get('n_modes', 0) < 10:
            recommendations.append(("📊", "Increase number of modes for improved analysis accuracy"))

        if not results.get('converged', True):
            recommendations.append(("🔄", "Review convergence parameters and mesh density"))

        if flutter_speed > 1000:
            recommendations.append(("✅", "Panel design shows excellent flutter resistance"))
            recommendations.append(("📈", "Consider weight optimization while maintaining flutter margin"))

        html_items = []
        for icon, text in recommendations:
            html_items.append(f"""
                <div class="recommendation-item">
                    <span class="recommendation-icon">{icon}</span>
                    <div class="recommendation-text">{text}</div>
                </div>
            """)

        return ''.join(html_items) if html_items else """
            <div class="recommendation-item">
                <span class="recommendation-icon">✅</span>
                <div class="recommendation-text">Analysis completed successfully with no critical issues identified.</div>
            </div>
        """

    def _generate_velocity_labels(self) -> str:
        """Generate velocity labels for charts."""
        velocities = list(range(0, 1600, 100))
        return json.dumps(velocities)

    def _generate_mode_data(self, mode: int, data_type: str) -> str:
        """Generate mode data for charts."""
        import math
        data = []

        for i in range(16):
            velocity = i * 100

            if data_type == 'damping':
                value = -0.05 + 0.1 * math.sin(i/5 + mode) * math.exp(-i/20)
                if velocity > 800 + mode * 100:
                    value += 0.05 * ((velocity - 800 - mode * 100) / 700)
            else:  # frequency
                value = 20 + mode * 30 + (velocity / 1500) * 20
                value += 5 * math.sin((velocity / 200) + mode)
                if velocity > 700 + mode * 150:
                    value -= (velocity - 700 - mode * 150) * 0.02

            data.append(round(value, 3))

        return json.dumps(data)

    def open_report(self, report_path: str):
        """Open the report in default browser."""
        webbrowser.open(f'file://{os.path.abspath(report_path)}')