# ############################################################################
# AI_HEADER: MODULE_MARKDOWN_REPORTER
# ROLE: Assemble markdown reports from sectioned content.
# DEPENDENCIES: pydantic.
# GRACE_ANCHORS: [REPORT_SCHEMA, REPORT_ASSEMBLY]
# ############################################################################

from typing import List

from pydantic import BaseModel, Field

# #START_BLOCK_REPORT_SCHEMA
class ReportSection(BaseModel):
    """
    # PURPOSE: Represent a report section for Markdown assembly.
    # INPUT: section_id, title, content.
    # OUTPUT: Validated section object.
    # CONTEXT: Used by the Markdown reporter.
    """

    section_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
# #END_BLOCK_REPORT_SCHEMA

# #START_BLOCK_REPORT_ASSEMBLY
def assemble_markdown(report_title: str, sections: List[ReportSection]) -> str:
    """
    # PURPOSE: Assemble the final Markdown report from sections.
    # INPUT: report_title (str), sections (list[ReportSection]).
    # OUTPUT: Markdown string for the final report.
    # CONTEXT: Used to build report content for DB/file storage.
    """

    header = f"# {report_title}\n\n"
    body = []
    for section in sections:
        body.append(f"## {section.title}\n\n{section.content}\n")
    return header + "\n".join(body).strip() + "\n"
# #END_BLOCK_REPORT_ASSEMBLY
