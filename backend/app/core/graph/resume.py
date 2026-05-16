from app.core.graph.builder import (
    build_graph
)


graph = build_graph()


async def resume_workflow(
    state
):

    config = {

        "configurable": {

            "thread_id":
                state.thread_id
        }
    }

    return await graph.ainvoke(
        state,
        config=config
    )