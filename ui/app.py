import os
import sys
import docx
import streamlit as st
import shutil
from datetime import datetime

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from versioning.manager import VersionManager
from versioning.validator import DocumentValidator
from versioning.diff import VersionDiff
from retrieval.context_assembler import ContextAssembler
from llm.client import GroqClient
from llm.prompts import QA_SYSTEM_PROMPT
from editing.operations import ReplaceText, InsertWarning, InsertCaution, ReplaceStep, AppendSubsection, UpdateTableCell
from editing.validator import EditValidator
from config.settings import settings

# Page Setup
st.set_page_config(
    page_title="Boeing 737-800 Maintenance RAG Chatbot",
    page_icon="✈️",
    layout="wide"
)

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "proposed_edit" not in st.session_state:
    st.session_state.proposed_edit = None
if "edit_error" not in st.session_state:
    st.session_state.edit_error = None
if "edit_success" not in st.session_state:
    st.session_state.edit_success = None

# Instantiate Managers
vm = VersionManager()
assembler = ContextAssembler()
llm_client = GroqClient()

# Header Area
st.title("✈️ Boeing 737-800 Document Intelligence System")
st.markdown(
    """
    This is a safety-adjacent document assistant. 
    Every response is grounded in the active document version, citing specific sections.
    """
)

# Layout Columns
col_chat, col_control = st.columns([3, 2])

# ==========================================
# LEFT COLUMN: Chat & Retrieval QA
# ==========================================
with col_chat:
    st.header("💬 Assistant Chat")
    
    # Display Chat History
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])
            if chat["role"] == "assistant" and "context" in chat:
                with st.expander("🔍 Show Retrieval Citations"):
                    # SQL
                    if chat["context"]["sql_query"]:
                        st.markdown(f"**SQL Query Executed:**\n`{chat['context']['sql_query']}`")
                        if chat["context"]["sql_results"]:
                            st.write(chat["context"]["sql_results"])
                        else:
                            st.caption("No SQL results returned.")
                    # RAG
                    st.markdown("**RAG Procedural Chunks Retrieved:**")
                    for chunk in chat["context"]["rag_chunks"]:
                        st.markdown(
                            f"- **{chunk['chunk_id']}** (Score: {chunk['rrf_score']:.4f})  \n"
                            f"  *Chapter: {chunk['chapter']} | Section: {chunk['section']} | Subsection: {chunk['subsection']}*  \n"
                            f"  ```text\n{chunk['text'][:250]}...\n  ```"
                        )

    # Chat Input
    query = st.chat_input("Ask a question about the maintenance manual...")
    if query:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": query})
        
        with st.chat_message("user"):
            st.markdown(query)
            
        with st.chat_message("assistant"):
            with st.spinner("Retrieving manual context and generating answer..."):
                # Assemble context
                context_data = assembler.assemble(query, top_k_rag=3)
                
                # Call Groq LLM
                try:
                    answer = llm_client.generate(
                        system_prompt=QA_SYSTEM_PROMPT,
                        user_prompt=context_data["user_prompt"],
                        temperature=0.0
                    )
                    st.markdown(answer)
                    # Add to session state history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "context": {
                            "sql_query": context_data["sql_query"],
                            "sql_results": context_data["sql_results"],
                            "rag_chunks": context_data["rag_chunks"]
                        }
                    })
                except Exception as e:
                    st.error(f"Error communicating with LLM: {str(e)}")

# ==========================================
# RIGHT COLUMN: Version Control & Document Editing
# ==========================================
with col_control:
    st.header("⚙️ Document Management")
    
    # Active Version Panel
    active_version = vm.get_active_version_id()
    st.subheader(f"Active Version: :green[{active_version}]")
    
    # Version History & Rollback Tabs
    tab_history, tab_edit, tab_diff = st.tabs(["📜 Version History", "✏️ Edit Manual", "📊 Version Diff"])
    
    with tab_history:
        st.markdown("### Historical Change Log")
        history = vm.get_history()
        
        for entry in history:
            is_active = entry["is_active"]
            st.markdown(
                f"**Version:** `{entry['version_id']}` "
                f"{'*(ACTIVE)*' if is_active else ''}  \n"
                f"**Author:** {entry['author']} | **Date:** {entry['timestamp']}  \n"
                f"**Description:** {entry['description']}  \n"
                f"**Filename:** `{entry['filename']}`"
            )
            
            # Action button to rollback
            if not is_active:
                if st.button(f"Activate/Rollback to {entry['version_id']}", key=f"rb_{entry['version_id']}"):
                    with st.spinner(f"Downgrading database and indexes to {entry['version_id']}..."):
                        vm.downgrade(entry["version_id"])
                        st.success(f"Successfully rolled back to version {entry['version_id']}.")
                        st.rerun()
            st.markdown("---")

    with tab_edit:
        st.markdown("### Apply Typed Document Edit")
        
        # Select operation
        op_type = st.selectbox(
            "Select Edit Operation Type",
            ["Insert Warning", "Replace Step", "Update Table Cell", "Append Subsection", "Replace Text"]
        )
        
        # Common parameters
        author = st.text_input("Author Name", value="maintenance_engineer")
        change_desc = st.text_area("Change Log Description", placeholder="Reason or context for the change...")
        
        # Operation-specific parameters
        if op_type == "Insert Warning":
            target_p_id = st.number_input("Target Paragraph ID (insert after)", min_value=0, step=1)
            warning_text = st.text_area("Warning Text")
            sec_name = st.text_input("Section Reference", value="1.5 Hazardous Materials")
            
        elif op_type == "Replace Step":
            sec_name = st.text_input("Section Name (e.g., '5.2.1 Tire Pressure Servicing')", value="5.2.1 Tire Pressure Servicing")
            step_num = st.text_input("Step Number (e.g. '1', '2', 'a')", value="1")
            step_text = st.text_area("New Step Content")
            
        elif op_type == "Update Table Cell":
            table_id = st.number_input("Table ID (0-based sequential table index)", min_value=0, step=1)
            row_idx = st.number_input("Row Index", min_value=0, step=1)
            col_idx = st.number_input("Column Index", min_value=0, step=1)
            new_value = st.text_input("New Cell Value")
            sec_name = st.text_input("Section Reference", value="Appendix A.2")
            
        elif op_type == "Append Subsection":
            sec_name = st.text_input("Parent Section Name", value="1.4 Lockout and Tagout (LOTO)")
            sub_heading = st.text_input("New Subsection Heading")
            sub_content = st.text_area("New Subsection Content")
            
        elif op_type == "Replace Text":
            target_p_id = st.number_input("Target Paragraph ID to replace", min_value=0, step=1)
            new_text = st.text_area("Replacement Text")
            sec_name = st.text_input("Section Reference", value="General")

        # Action Buttons
        if st.button("Validate & Preview Edit"):
            # Load active path to validate
            active_docx = vm.get_active_docx_path()
            
            try:
                # Perform pre-edit dry run checks
                if op_type == "Insert Warning":
                    EditValidator.validate_insert_warning(active_docx, target_p_id)
                    st.session_state.proposed_edit = {
                        "op_class": InsertWarning,
                        "args": (target_p_id, warning_text, sec_name, change_desc),
                        "meta": {"operation": "InsertWarning", "description": change_desc, "section": sec_name}
                    }
                elif op_type == "Replace Step":
                    EditValidator.validate_replace_step(active_docx, sec_name, step_num)
                    st.session_state.proposed_edit = {
                        "op_class": ReplaceStep,
                        "args": (sec_name, step_num, step_text, change_desc),
                        "meta": {"operation": "ReplaceStep", "description": change_desc, "section": sec_name}
                    }
                elif op_type == "Update Table Cell":
                    EditValidator.validate_update_table_cell(active_docx, table_id, row_idx, col_idx)
                    st.session_state.proposed_edit = {
                        "op_class": UpdateTableCell,
                        "args": (table_id, row_idx, col_idx, new_value, sec_name, change_desc),
                        "meta": {"operation": "UpdateTableCell", "description": change_desc, "section": sec_name}
                    }
                elif op_type == "Append Subsection":
                    EditValidator.validate_append_subsection(active_docx, sec_name)
                    st.session_state.proposed_edit = {
                        "op_class": AppendSubsection,
                        "args": (sec_name, sub_heading, sub_content, change_desc),
                        "meta": {"operation": "AppendSubsection", "description": change_desc, "section": sec_name}
                    }
                elif op_type == "Replace Text":
                    EditValidator.validate_replace_text(active_docx, target_p_id)
                    st.session_state.proposed_edit = {
                        "op_class": ReplaceText,
                        "args": (target_p_id, new_text, sec_name, change_desc),
                        "meta": {"operation": "ReplaceText", "description": change_desc, "section": sec_name}
                    }
                
                st.session_state.edit_error = None
                st.success("Dry run validation PASSED. Ready to commit.")
                
            except Exception as e:
                st.session_state.proposed_edit = None
                st.session_state.edit_error = f"Validation Failed: {str(e)}"
                st.error(st.session_state.edit_error)
                
        # Commit Dialog
        if st.session_state.proposed_edit:
            st.markdown("### Proposed Commit Details:")
            st.info(
                f"**Operation**: {st.session_state.proposed_edit['meta']['operation']}  \n"
                f"**Section**: {st.session_state.proposed_edit['meta']['section']}  \n"
                f"**Description**: {st.session_state.proposed_edit['meta']['description']}  \n"
                f"**Author**: {author}"
            )
            
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("Confirm & Commit to Head", type="primary"):
                    with st.spinner("Applying changes, validating DOCX, and rebuilding indexes..."):
                        # Get active docx, copy to temp, apply operation, check, upgrade
                        active_docx = vm.get_active_docx_path()
                        temp_path = os.path.join(settings.DATA_DIR, "temp_ui_edits.docx")
                        shutil.copy(active_docx, temp_path)
                        
                        try:
                            doc = docx.Document(temp_path)
                            op_class = st.session_state.proposed_edit["op_class"]
                            args = st.session_state.proposed_edit["args"]
                            
                            # Instantiate and apply
                            op = op_class(*args)
                            op.apply(doc)
                            doc.save(temp_path)
                            
                            # Pre-commit validate
                            DocumentValidator.validate_docx(temp_path)
                            
                            # Create new version ID based on history length
                            new_v_id = f"v{len(vm.get_history()) + 1}"
                            
                            vm.upgrade(
                                new_version_id=new_v_id,
                                author=author,
                                description=f"Upgrade: {st.session_state.proposed_edit['meta']['description']}",
                                changes=[st.session_state.proposed_edit["meta"]],
                                temp_docx_path=temp_path
                            )
                            
                            st.session_state.proposed_edit = None
                            st.session_state.edit_success = f"Successfully committed version {new_v_id}."
                            st.toast(st.session_state.edit_success)
                            st.rerun()
                            
                        except Exception as ex:
                            st.error(f"Commit Failed during save or index: {str(ex)}")
                        finally:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                                
            with col_cancel:
                if st.button("Cancel Proposed Edit"):
                    st.session_state.proposed_edit = None
                    st.rerun()

    with tab_diff:
        st.markdown("### Generate Version Diff Report")
        v_a = st.selectbox("Compare Version A", [entry["version_id"] for entry in vm.get_history()], index=0)
        v_b = st.selectbox("Compare Version B", [entry["version_id"] for entry in vm.get_history()], index=len(vm.get_history()) - 1)
        
        if st.button("Generate Diff Report"):
            try:
                report = VersionDiff.get_diff(v_a, v_b)
                st.code(report, language="text")
            except Exception as e:
                st.error(f"Error generating diff: {str(e)}")
