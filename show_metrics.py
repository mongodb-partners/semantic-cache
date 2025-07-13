import asyncio
from datetime import datetime
import httpx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

def create_enhanced_metrics_dashboard(data):
    """Create a visually enhanced metrics dashboard with proper spacing"""
    
    # Set up modern styling with emoji-compatible fonts
    plt.style.use('default')
    # Try to use system fonts that support emojis, fallback to sans-serif
    try:
        plt.rcParams['font.family'] = ['Segoe UI', 'DejaVu Sans', 'Arial', 'sans-serif']
    except:
        plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 9
    
    # Create figure
    fig = plt.figure(figsize=(20, 14), facecolor='#f8f9fa')
    gs = fig.add_gridspec(3, 4, 
                         hspace=0.6,  # Increased vertical spacing
                         wspace=0.4,  # Increased horizontal spacing
                         left=0.06, right=0.94, 
                         top=0.88, bottom=0.10)  # Adjusted margins
    
    # Color palette
    colors = {
        'primary': '#2c3e50',
        'success': '#27ae60',
        'warning': '#f39c12',
        'danger': '#e74c3c',
        'info': '#3498db',
        'purple': '#9b59b6',
        'teal': '#16a085'
    }
    
    # Extract data
    uptime_seconds = data.get('uptime_seconds', 0)
    counters = data.get('counters', {})
    gauges = data.get('gauges', {})
    histograms = data.get('histograms', {})
    
    # 1. System Uptime
    ax1 = fig.add_subplot(gs[0, 0])
    uptime_hours = uptime_seconds / 3600
    uptime_minutes = (uptime_seconds % 3600) / 60
    
    bars = ax1.bar(['Uptime'], [uptime_hours], color=colors['success'], alpha=0.8, width=0.5)
    ax1.set_ylabel('Hours', fontweight='bold', color=colors['primary'])
    ax1.set_title('System Uptime', fontweight='bold', fontsize=11, 
                  color=colors['primary'], pad=15)
    
    # Add value text
    ax1.text(0, uptime_hours/2, f'{uptime_hours:.1f}h\n{uptime_minutes:.0f}m', 
             ha='center', va='center', fontweight='bold', fontsize=10, color='white')
    
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 2. Performance Counters - Single row
    ax2 = fig.add_subplot(gs[0, 1:3])  # Span 2 columns
    
    if counters:
        # Extract counter names and values more intelligently
        counter_items = list(counters.items())
        counter_names = []
        counter_values = []
        
        for key, value in counter_items:
            if 'vector_search' in key:
                counter_names.append('Vector\nSearch')
            elif 'cache_requests' in key:
                counter_names.append('Cache\nRequests')
            elif 'cache_writes' in key:
                counter_names.append('Cache\nWrites')
            else:
                # Generic fallback
                counter_names.append(key.replace('_', '\n').title())
            counter_values.append(value)
        
        counter_colors = [colors['info'], colors['warning']][:len(counter_names)]
        
        bars = ax2.bar(range(len(counter_names)), counter_values, 
                      color=counter_colors, alpha=0.8, width=0.6)
        
        ax2.set_xticks(range(len(counter_names)))
        ax2.set_xticklabels(counter_names, fontweight='bold', color=colors['primary'])
        ax2.set_ylabel('Count', fontweight='bold', color=colors['primary'])
        ax2.set_title('Performance Counters', fontweight='bold', fontsize=11, 
                      color=colors['primary'], pad=15)
        
        # Value labels
        max_val = max(counter_values) if counter_values else 1
        for i, (bar, value) in enumerate(zip(bars, counter_values)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.05, 
                     f'{value:,}', ha='center', va='bottom', fontweight='bold', 
                     fontsize=9, color=colors['primary'])
        
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 3. Gauge - Circular design
    ax3 = fig.add_subplot(gs[0, 3])
    if gauges:
        gauge_value = list(gauges.values())[0]
        gauge_name = "Candidates" #list(gauges.keys())[0].replace('_', ' ').title()
        
        # Create circular gauge
        circle = plt.Circle((0.5, 0.5), 0.35, color=colors['info'], 
                          alpha=0.8, transform=ax3.transAxes)
        ax3.add_patch(circle)
        
        inner_circle = plt.Circle((0.5, 0.5), 0.22, color='white', 
                                transform=ax3.transAxes)
        ax3.add_patch(inner_circle)
        
        ax3.text(0.5, 0.65, gauge_name, ha='center', va='center', 
                 transform=ax3.transAxes, fontsize=9, fontweight='bold', 
                 color=colors['primary'])
        ax3.text(0.5, 0.35, str(gauge_value), ha='center', va='center', 
                 transform=ax3.transAxes, fontsize=18, fontweight='bold', 
                 color=colors['info'])
    
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.axis('off')
    ax3.set_title('Active Gauge', fontweight='bold', fontsize=11, 
                  color=colors['primary'], pad=15)
    
    # 4. Vector Search Latency
    if 'vector_search_latency_ms' in histograms:
        ax4 = fig.add_subplot(gs[1, 0:2])  # Span 2 columns
        vs_data = histograms['vector_search_latency_ms']
        
        metrics = ['Min', 'P50', 'Avg', 'P95', 'P99', 'Max']
        values = [vs_data['min'], vs_data['p50'], vs_data['avg'], 
                 vs_data['p95'], vs_data['p99'], vs_data['max']]
        
        bars = ax4.bar(metrics, values, color=colors['info'], alpha=0.7, width=0.6)
        
        ax4.set_ylabel('Latency (ms)', fontweight='bold', color=colors['primary'])
        ax4.set_title('Vector Search Latency', fontweight='bold', fontsize=11, 
                      color=colors['primary'], pad=15)
        
        # Add value labels
        max_val = max(values) if values else 1
        for bar, value in zip(bars, values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.03, 
                     f'{value:.1f}', ha='center', va='bottom', fontweight='bold', 
                     fontsize=8, color=colors['primary'])
        
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)
        ax4.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 5. Query Latency
    query_latency_key = next((k for k in histograms.keys() if 'query_latency' in k), None)
    if query_latency_key:
        ax5 = fig.add_subplot(gs[1, 2:4])  # Span 2 columns
        ql_data = histograms[query_latency_key]
        
        metrics = ['Min', 'P50', 'Avg', 'P95', 'P99', 'Max']
        values = [ql_data['min'], ql_data['p50'], ql_data['avg'], 
                 ql_data['p95'], ql_data['p99'], ql_data['max']]
        
        bars = ax5.bar(metrics, values, color=colors['warning'], alpha=0.7, width=0.6)
        
        ax5.set_ylabel('Latency (ms)', fontweight='bold', color=colors['primary'])
        ax5.set_title('Query Latency', fontweight='bold', fontsize=11, 
                      color=colors['primary'], pad=15)
        
        max_val = max(values) if values else 1
        for bar, value in zip(bars, values):
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.03, 
                     f'{value:.1f}', ha='center', va='bottom', fontweight='bold', 
                     fontsize=8, color=colors['primary'])
        
        ax5.spines['top'].set_visible(False)
        ax5.spines['right'].set_visible(False)
        ax5.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 6. Similarity Score - Circular progress
    similarity_key = next((k for k in histograms.keys() if 'similarity' in k), None)
    if similarity_key:
        ax6 = fig.add_subplot(gs[2, 0])
        sim_data = histograms[similarity_key]
        similarity_score = sim_data['avg']
        
        # Create progress ring
        bg_circle = plt.Circle((0.5, 0.5), 0.3, fill=False, 
                              color='lightgray', linewidth=8, transform=ax6.transAxes)
        ax6.add_patch(bg_circle)
        
        # Progress indication (simplified without complex arc drawing)
        progress_circle = plt.Circle((0.5, 0.5), 0.3, fill=False,
                                   color=colors['success'], linewidth=8, 
                                   alpha=similarity_score, transform=ax6.transAxes)
        ax6.add_patch(progress_circle)
        
        ax6.text(0.5, 0.6, 'Similarity', ha='center', va='center', 
                 transform=ax6.transAxes, fontsize=9, fontweight='bold', 
                 color=colors['primary'])
        ax6.text(0.5, 0.4, f'{similarity_score:.3f}', ha='center', va='center', 
                 transform=ax6.transAxes, fontsize=14, fontweight='bold', 
                 color=colors['success'])
        
        ax6.set_xlim(0, 1)
        ax6.set_ylim(0, 1)
        ax6.axis('off')
        ax6.set_title('Similarity Score', fontweight='bold', fontsize=11, 
                      color=colors['primary'], pad=15)
    
    # 7. Latency Comparison
    if 'vector_search_latency_ms' in histograms and query_latency_key:
        ax7 = fig.add_subplot(gs[2, 1:3])  # Span 2 columns
        
        vs_data = histograms['vector_search_latency_ms']
        ql_data = histograms[query_latency_key]
        
        comparison_metrics = ['Average', 'P95', 'P99']
        vector_search = [vs_data['avg'], vs_data['p95'], vs_data['p99']]
        query_latency = [ql_data['avg'], ql_data['p95'], ql_data['p99']]
        
        x = np.arange(len(comparison_metrics))
        width = 0.35
        
        ax7.bar(x - width/2, vector_search, width, label='Vector Search', 
                color=colors['info'], alpha=0.8)
        ax7.bar(x + width/2, query_latency, width, label='Query Latency', 
                color=colors['danger'], alpha=0.8)
        
        ax7.set_ylabel('Latency (ms)', fontweight='bold', color=colors['primary'])
        ax7.set_title('Latency Comparison', fontweight='bold', fontsize=11, 
                      color=colors['primary'], pad=15)
        ax7.set_xticks(x)
        ax7.set_xticklabels(comparison_metrics)
        ax7.legend(fontsize=8)
        ax7.spines['top'].set_visible(False)
        ax7.spines['right'].set_visible(False)
        ax7.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 8. Summary Card
    ax8 = fig.add_subplot(gs[2, 3])
    ax8.axis('off')
    
    # Create summary card background
    card = FancyBboxPatch((0.05, 0.1), 0.9, 0.8, boxstyle="round,pad=0.05",
                         facecolor='white', edgecolor=colors['primary'], 
                         linewidth=1, alpha=0.9, transform=ax8.transAxes)
    ax8.add_patch(card)
    
    # Calculate summary statistics
    total_requests = 0
    counter_items = list(counters.items())
    for key, value in counter_items:
            if 'cache_requests' in key or 'cache_writes' in key:
                total_requests+=value
    avg_vector_latency = histograms.get('vector_search_latency_ms', {}).get('avg', 0)
    status_text = 'Healthy' if uptime_hours > 0 else 'Down'
    status_symbol = '●' if uptime_hours > 0 else '○'  # Use simple symbols instead of emojis
    
    summary_text = f"""SYSTEM SUMMARY
Uptime: {uptime_hours:.1f}h
Requests: {total_requests:,}
Avg Vector: {avg_vector_latency:.1f}ms
Candidates: {gauges.get('last_num_candidates', 'N/A')}
Status: {status_text} {status_symbol}"""
    
    ax8.text(0.1, 0.8, summary_text, transform=ax8.transAxes, fontsize=9, 
             verticalalignment='top', fontfamily='monospace', 
             color=colors['primary'])
    
    # Add main title
    fig.suptitle('System Metrics Dashboard', fontsize=16, fontweight='bold', 
                y=0.94, color=colors['primary'])
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fig.text(0.99, 0.02, f'Generated: {timestamp}', ha='right', va='bottom', 
             fontsize=9, style='italic', transform=fig.transFigure, 
             color=colors['primary'], alpha=0.7)
    
    # Use subplots_adjust instead of tight_layout to avoid warnings
    plt.subplots_adjust(left=0.06, right=0.94, top=0.88, bottom=0.10)
    plt.savefig('plot.png', 
            dpi=300,          # High resolution
            bbox_inches='tight',  # Remove extra whitespace
            facecolor='white',    # Background color
            edgecolor='none')     # No border


async def test():
    """Test function to fetch and display metrics."""
    base_url = "http://localhost:8183"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🚀 Testing Semantic Cache Service")
        print("-" * 40)
        
        try:
            # Test 1: Health check
            print("1. Testing health check...")
            response = await client.get(f"{base_url}/health/detailed")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   Service Status: {health_data.get('status', 'unknown')}")
                print(f"   MongoDB: {health_data.get('checks', {}).get('mongodb', 'unknown')}")
                print(f"   Embedding Service: {health_data.get('checks', {}).get('embedding_service', 'unknown')}")
            else:
                print(f"   Error: {response.text}")
            print()
           
            # Test 2: Get Metrics
            print("2. Testing get metrics...")
            response = await client.get(f"{base_url}/metrics")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                metrics_data = response.json()
                print(f"   Uptime: {metrics_data.get('uptime_seconds', 0):.1f} seconds")
                print(f"   Counters: {len(metrics_data.get('counters', {}))}")
                print(f"   Gauges: {len(metrics_data.get('gauges', {}))}")
                print(f"   Histograms: {len(metrics_data.get('histograms', {}))}")
                
                # Create the dashboard
                create_enhanced_metrics_dashboard(metrics_data)
            else:
                print(f"   Error: {response.text}")
            print()
            
        except httpx.ConnectError:
            print("❌ Could not connect to the service. Make sure it's running on localhost:8183")
        except Exception as e:
            print(f"❌ Error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test())