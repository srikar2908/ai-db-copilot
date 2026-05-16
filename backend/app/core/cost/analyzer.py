from sqlalchemy.ext.asyncio import (
    create_async_engine
)

from sqlalchemy import text

from app.core.cost.models import (
    QueryCostAnalysis
)


# -------------------------------------------------
# ANALYZE QUERY COST
# -------------------------------------------------

async def analyze_query_cost(

    database_url: str,

    sql: str
) -> QueryCostAnalysis:

    engine = create_async_engine(
        database_url,
        connect_args={
        "statement_cache_size": 0
    }
    )

    try:

        async with engine.connect() as conn:

            # -----------------------------------------
            # SQLITE SUPPORT
            # -----------------------------------------

            if "sqlite" in database_url:

                explain_sql = (
                    f"EXPLAIN QUERY PLAN {sql}"
                )

                result = await conn.execute(
                    text(explain_sql)
                )

                rows = result.fetchall()

                raw_plan = str(rows)

                warnings = []

                risk_level = "low"

                # -------------------------------------
                # DETECT FULL TABLE SCAN
                # -------------------------------------

                for row in rows:

                    row_text = str(row).upper()

                    if "SCAN" in row_text:

                        warnings.append(
                            "Possible full table scan detected"
                        )

                        risk_level = "medium"

                return QueryCostAnalysis(

                    success=True,

                    estimated_cost=None,

                    estimated_rows=None,

                    risk_level=risk_level,

                    warnings=warnings,

                    raw_plan=raw_plan
                )

            # -----------------------------------------
            # POSTGRES SUPPORT
            # -----------------------------------------

            elif "postgresql" in database_url:

                explain_sql = (
                    f"EXPLAIN (FORMAT JSON) {sql}"
                )

                result = await conn.execute(
                    text(explain_sql)
                )

                row = result.fetchone()

                plan_data = row[0][0]

                plan = plan_data["Plan"]

                estimated_cost = plan.get(
                    "Total Cost",
                    0
                )

                estimated_rows = plan.get(
                    "Plan Rows",
                    0
                )

                warnings = []

                risk_level = "low"

                # -------------------------------------
                # COST THRESHOLDS
                # -------------------------------------

                if estimated_cost > 10000:

                    risk_level = "high"

                    warnings.append(
                        "Very high query cost detected"
                    )

                elif estimated_cost > 1000:

                    risk_level = "medium"

                    warnings.append(
                        "Moderate query cost detected"
                    )

                # -------------------------------------
                # ROW THRESHOLDS
                # -------------------------------------

                if estimated_rows > 100000:

                    warnings.append(
                        "Large row scan detected"
                    )

                    if risk_level == "low":

                        risk_level = "medium"

                return QueryCostAnalysis(

                    success=True,

                    estimated_cost=estimated_cost,

                    estimated_rows=estimated_rows,

                    risk_level=risk_level,

                    warnings=warnings,

                    raw_plan=str(plan_data)
                )

            # -----------------------------------------
            # UNKNOWN DATABASE
            # -----------------------------------------

            return QueryCostAnalysis(

                success=False,

                estimated_cost=None,

                estimated_rows=None,

                risk_level="unknown",

                warnings=[
                    "Unsupported database type"
                ],

                raw_plan=None
            )

    except Exception as e:

        return QueryCostAnalysis(

            success=False,

            estimated_cost=None,

            estimated_rows=None,

            risk_level="unknown",

            warnings=[
                str(e)
            ],

            raw_plan=None
        )

    finally:

        await engine.dispose()