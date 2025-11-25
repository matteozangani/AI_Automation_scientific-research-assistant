# All'inizio del file, aggiungi import
from agent.paper_ranking_agent import call_ranking_agent

# Modifica il metodo search_executor_node (riga ~364)
async def search_executor_node(self, state: RAGAgentState) -> RAGAgentState:
    """Execute paper search"""
    logger.info("🔧 SEARCH EXECUTOR NODE: Executing paper search...")
    
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        logger.warning("⚠️ No tool calls found")
        return state
    
    # Execute tool calls
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Get MORE papers than needed for ranking
        search_limit = self.max_papers * 2  # Get 20 papers
        
        if 'max_results' in tool_args:
            tool_args['max_results'] = min(tool_args['max_results'], search_limit)
        else:
            tool_args['max_results'] = search_limit
        
        logger.info(f"⚙️ Executing {tool_name} with args: {tool_args}")
        
        if tool_name == "search_papers_tool":
            result = await search_papers_tool.ainvoke(tool_args)
            
            # ============= A2A RANKING =============
            if result.get('results'):
                logger.info(f"📊 Retrieved {len(result['results'])} papers")
                logger.info(f"🤖 Calling Ranking Agent (A2A)...")
                
                # Call specialist ranking agent
                ranked_papers, ranking_explanation = await call_ranking_agent(
                    papers=result['results'],
                    query=state["current_task"],
                    max_papers=self.max_papers,
                    api_key=self.api_key
                )
                
                # Update results with ranked papers
                result['results'] = ranked_papers
                result['ranking_explanation'] = ranking_explanation
                
                logger.info(f"✅ Papers ranked by specialist agent")
                logger.info(f"📝 Ranking explanation: {ranking_explanation[:100]}...")
            
            state["search_results"] = result
            
            # Add tool response
            state["messages"].append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
            )
    
    logger.info("✅ Search execution complete")
    return state
