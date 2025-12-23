import typer
import uuid
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, IntPrompt

# Import Core Domain Entities
from chimera_nexus.core.domain import (
    HybridThreatChain, 
    HybridNode, 
    HybridEdge,
    ThreatDomain, 
    RelationType
)

# Import Infrastructure Layers
from chimera_nexus.storage.repository import NexusRepository, StorageError
from chimera_nexus.analysis.auditor import CognitiveAuditor
from chimera_nexus.reporting.engine import ReportEngine

# Initialize System
app = typer.Typer(
    name="CHIMERA Nexus",
    help="Contextual Hybrid Intelligence for Monitoring, Evaluation & Risk Assessment",
    add_completion=False
)
console = Console()
repo = NexusRepository()

# --- Helper Functions (UI Logic) ---

def _render_chain_details(chain: HybridThreatChain):
    """
    Renders a comprehensive situational report to the terminal.
    """
    iap = chain.calculate_iap(urgency=5.0)  # Default urgency baseline
    ccs = chain.coherence_score
    
    # Header Panel
    console.print(Panel.fit(
        f"[bold cyan]ID:[/bold cyan] {chain.id}\n"
        f"[bold cyan]Nodes:[/bold cyan] {len(chain.nodes)} | [bold cyan]Edges:[/bold cyan] {len(chain.edges)}\n"
        f"[bold red]IAP (Pressure):[/bold red] {iap:.2f} | [bold green]Coherence:[/bold green] {ccs:.2f}",
        title=f"NEXUS REPORT: {chain.name.upper()}",
        border_style="blue"
    ))

    # Nodes Table
    if chain.nodes:
        table = Table(title="Detected Signals (Nodes)", expand=True)
        table.add_column("Idx", justify="right", style="dim")
        table.add_column("Domain", style="magenta")
        table.add_column("Type", style="white")
        table.add_column("Conf.", justify="right")
        table.add_column("Description", style="dim")
        
        # Sort by timestamp for chronological view
        sorted_nodes = sorted(chain.nodes.values(), key=lambda x: x.timestamp)
        
        for idx, n in enumerate(sorted_nodes):
            conf_style = "green" if n.confidence > 0.7 else "yellow" if n.confidence > 0.4 else "red"
            table.add_row(
                str(idx + 1),
                n.domain.value, 
                n.signal_type, 
                f"[{conf_style}]{n.confidence}[/]",
                n.description
            )
        console.print(table)
    else:
        console.print("[italic yellow]No signals collected yet.[/italic yellow]")

    # Edges (Links) Summary
    if chain.edges:
        console.print(f"\n[bold]Active Links ({len(chain.edges)}):[/bold]")
        for edge in chain.edges:
            # Simple lookup for display (in prod, optimize this look-up)
            src = chain.nodes.get(edge.source_id)
            tgt = chain.nodes.get(edge.target_id)
            if src and tgt:
                console.print(f"  └─ [cyan]{src.signal_type}[/] ==({edge.relation_type.value})==> [cyan]{tgt.signal_type}[/]")

def _select_node_interactive(chain: HybridThreatChain, prompt_text: str) -> Optional[HybridNode]:
    """
    Helper to pick a node from a list using a simple index number.
    """
    nodes = list(chain.nodes.values())
    # Sort for consistent indexing
    nodes.sort(key=lambda x: x.timestamp)
    
    if not nodes:
        return None
    
    console.print(f"\n[bold]{prompt_text}[/bold]")
    for idx, node in enumerate(nodes):
        console.print(f"  [bold cyan]{idx + 1}.[/] [{node.domain.value}] {node.signal_type} ({node.description[:30]}...)")
    
    choice = IntPrompt.ask("Select Number", choices=[str(i+1) for i in range(len(nodes))])
    return nodes[int(choice) - 1]

# --- CLI Commands ---

@app.command()
def init(name: str):
    """
    Initialize a new Hybrid Threat Chain (HTC) context.
    """
    try:
        chain = HybridThreatChain(name=name)
        path = repo.save_chain(chain)
        console.print(f"[bold green]SUCCESS:[/bold green] Initialized Nexus chain '[white]{name}[/]'")
        console.print(f"Storage: {path}")
    except Exception as e:
        console.print(f"[bold red]FAILURE:[/bold red] {e}")

@app.command("list")
def list_chains():
    """
    List all active threat contexts in the registry.
    """
    chains = repo.list_chains()
    if not chains:
        console.print("[yellow]No active chains found.[/yellow]")
        return

    table = Table(title="CHIMERA Nexus Registry")
    table.add_column("ID (Short)", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Domains")
    table.add_column("Nodes", justify="right")
    table.add_column("Pressure (IAP)", justify="right")

    for c in chains:
        domains = ", ".join([d.value[:3] for d in c.domain_mix])
        iap = c.calculate_iap(urgency=5.0)
        table.add_row(str(c.id)[:8], c.name, domains, str(len(c.nodes)), f"{iap:.2f}")
    
    console.print(table)

@app.command()
def add_signal(chain_id: str):
    """
    Add a minimal viable signal (Node) to a chain.
    """
    try:
        # 1. Load Chain
        full_uuid = uuid.UUID(chain_id)
        chain = repo.load_chain(full_uuid)
        
        console.print(f"[bold]Adding Signal to:[/bold] {chain.name}")
        
        # 2. Interactive Collection
        domain = Prompt.ask("Domain", choices=[d.value for d in ThreatDomain])
        sig_type = Prompt.ask("Signal Type (e.g. ddos, misinformation)")
        desc = Prompt.ask("Description")
        conf = FloatPrompt.ask("Confidence (0.0 - 1.0)", default=0.5)
        
        # 3. Create Node
        node = HybridNode(
            domain=ThreatDomain(domain),
            signal_type=sig_type,
            description=desc,
            confidence=conf
        )
        
        # 4. Update & Save
        chain.add_node(node)
        repo.save_chain(chain)
        console.print("[green]Signal Integrated.[/green]")
        
    except (ValueError, StorageError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def link(chain_id: str):
    """
    Create a causal link (Edge) between two signals. 
    Turns a list of events into a 'Chain'.
    """
    try:
        full_uuid = uuid.UUID(chain_id)
        chain = repo.load_chain(full_uuid)
        
        if len(chain.nodes) < 2:
            console.print("[yellow]Need at least 2 signals to create a link.[/yellow]")
            return

        source = _select_node_interactive(chain, "Select SOURCE Signal (Cause)")
        target = _select_node_interactive(chain, "Select TARGET Signal (Effect)")

        if source.id == target.id:
            console.print("[red]Cannot link a signal to itself.[/red]")
            return

        rel_type = Prompt.ask("Relationship Type", choices=[r.value for r in RelationType])
        weight = FloatPrompt.ask("Connection Strength (0.0 - 1.0)", default=1.0)
        justification = Prompt.ask("Justification (Why linked?)")

        edge = HybridEdge(
            source_id=source.id,
            target_id=target.id,
            relation_type=RelationType(rel_type),
            weight=weight,
            justification=justification
        )
        
        chain.add_edge(edge)
        repo.save_chain(chain)
        console.print(f"[green]✓[/green] Linked: [cyan]{source.signal_type}[/] -> [cyan]{target.signal_type}[/]")

    except (ValueError, StorageError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def inspect(chain_id: str):
    """
    Deep dive into a specific chain structure.
    """
    try:
        full_uuid = uuid.UUID(chain_id)
        chain = repo.load_chain(full_uuid)
        _render_chain_details(chain)
    except Exception as e:
        console.print(f"[bold red]Lookup Failed:[/bold red] {e}")

@app.command()
def audit(chain_id: str):
    """
    Run the Cognitive Auditor (Red Team) on the chain.
    Detects bias, logical gaps, and overconfidence.
    """
    try:
        full_uuid = uuid.UUID(chain_id)
        chain = repo.load_chain(full_uuid)
        
        auditor = CognitiveAuditor()
        findings = auditor.audit(chain)
        
        console.print(Panel(f"[bold]Cognitive Audit Report: {chain.name}[/bold]", style="white on blue"))
        
        if not findings:
            console.print("\n[bold green]✓ No structural biases detected.[/bold green]")
        else:
            table = Table(title="Detected Anomalies", show_lines=True)
            table.add_column("Bias Type", style="red")
            table.add_column("Severity", justify="right")
            table.add_column("Remediation Hint", style="yellow")
            
            for f in findings:
                sev_style = "bold red" if f.severity > 0.7 else "yellow"
                table.add_row(
                    f.bias_type.value.upper(),
                    f"[{sev_style}]{f.severity:.2f}[/]",
                    f"{f.description}\n[italic]Fix: {f.remediation_hint}[/italic]"
                )
            console.print(table)
            
    except Exception as e:
        console.print(f"[bold red]Audit Failed:[/bold red] {e}")

@app.command()
def export(chain_id: str, format: str = typer.Option("md", help="Format: 'md' for Markdown, 'dot' for Graphviz")):
    """
    Generate decision-support artifacts (Reports/Graphs).
    """
    try:
        full_uuid = uuid.UUID(chain_id)
        chain = repo.load_chain(full_uuid)
        
        # Always Audit before Exporting
        auditor = CognitiveAuditor()
        findings = auditor.audit(chain)
        
        engine = ReportEngine()
        filename = f"{chain.name.replace(' ', '_').lower()}_{str(chain.id)[:8]}"
        
        if format.lower() == "md":
            content = engine.generate_markdown_report(chain, findings)
            out_path = f"{filename}.md"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[green]✓[/green] Executive Report generated: [bold]{out_path}[/bold]")
            
        elif format.lower() == "dot":
            content = engine.generate_graphviz_dot(chain)
            out_path = f"{filename}.dot"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[green]✓[/green] Graphviz definition generated: [bold]{out_path}[/bold]")
            console.print("[dim]Tip: Use 'dot -Tpng input.dot -o output.png' to render image.[/dim]")
            
        else:
            console.print(f"[red]Unknown format: {format}[/red]")

    except Exception as e:
        console.print(f"[bold red]Export Failed:[/bold red] {e}")

@app.command()
def simulate_scenario():
    """
    Generates a realistic 'Mock' Hybrid Threat Chain for training purposes.
    """
    try:
        scenario_name = f"Exercise_Blue_Sky_{uuid.uuid4().hex[:4]}"
        chain = HybridThreatChain(name=scenario_name)
        
        console.print(f"[bold]Generating Training Scenario:[/bold] {scenario_name}...")

        # 1. Create Nodes
        n1 = HybridNode(
            domain=ThreatDomain.INFORMATION, 
            signal_type="social_media_rumor", 
            confidence=0.6, 
            description="Leaked false documents about bank solvency."
        )
        n2 = HybridNode(
            domain=ThreatDomain.CYBER, 
            signal_type="ddos_probe", 
            confidence=0.9, 
            description="High traffic on banking login portal."
        )
        n3 = HybridNode(
            domain=ThreatDomain.ECONOMIC, 
            signal_type="stock_dip", 
            confidence=0.8, 
            description="Bank stock drops 4% in pre-market."
        )
        
        chain.add_node(n1)
        chain.add_node(n2)
        chain.add_node(n3)

        # 2. Link Nodes
        chain.add_edge(HybridEdge(
            source_id=n1.id, 
            target_id=n3.id, 
            relation_type=RelationType.TRIGGERING, 
            justification="Panic selling driven by rumor."
        ))
        
        chain.add_edge(HybridEdge(
            source_id=n2.id, 
            target_id=n1.id, 
            relation_type=RelationType.AMPLIFICATION, 
            justification="Service outage validates the fake documents."
        ))

        path = repo.save_chain(chain)
        console.print(f"[green]✓[/green] Scenario created at: {path}")
        console.print(f"Use [bold]python -m chimera_nexus.cli.main inspect {chain.id}[/bold] to view.")

    except Exception as e:
        console.print(f"[red]Simulation failed:[/red] {e}")

if __name__ == "__main__":
    app()