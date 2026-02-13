
import os
import asyncio
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
# Use the exact class name you identified
from packages.orchestrator.agent import orchestratorAgent 

async def run_dry_run():
    langfuse = Langfuse()
    # Instantiate your orchestrator class
    agent_platform = orchestratorAgent() 
    
    # Fetch your GAIA dataset
    dataset = langfuse.get_dataset("GAIA-node-reasoning-levels-123-v2")
    test_item = dataset.items[0]
    
    # item.run() links the execution to the dataset in Langfuse UI
    with test_item.run(run_name="Architecture_Mirror_Test") as experiment_run:
        # The CallbackHandler instruments every internal node (plan, thought, reflect)
        handler = CallbackHandler()
        
        # Initial state must match what your plan_node expects
        initial_input = {"messages": [("user", test_item.input["question"])]}
        
        # Invoke the graph exactly as in production
        # We use await because your _build_workflow_graph is async
        final_state = await agent_platform.graph.ainvoke(
            initial_input,
            config={"callbacks": [handler]}
        )
        
        # Extract response from your generate_final_response_node
        actual_output = final_state.get("final_response", "No response")
        
        # Update the experiment entry for comparison against the golden record
        experiment_run.update(output=actual_output)
        print(f"Success! Output: {actual_output}")

if __name__ == "__main__":
    asyncio.run(run_dry_run())