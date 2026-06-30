import re
from typing import List, Dict, Optional
from processing.models import DocumentElement, Chunk, ContentType, ProcedurePhase

class Chunker:
    @staticmethod
    def chunk_document(elements: List[DocumentElement], version_id: str) -> List[Chunk]:
        """
        Chunks the document elements into List[Chunk] according to section hierarchy,
        coupling warning/caution/note tables with their preceding steps, and grouping steps.
        """
        chunks = []
        
        # 1. Group elements by subsection/section/chapter hierarchy.
        # We can construct a hierarchy key: (chapter, section, subsection)
        groups: Dict[tuple, List[DocumentElement]] = {}
        for el in elements:
            # Skip lookup tables as they go to SQL
            if el.content_type == ContentType.TABLE_LOOKUP:
                continue
            
            key = (el.chapter, el.section, el.subsection)
            if key not in groups:
                groups[key] = []
            groups[key].append(el)

        for key, group_els in groups.items():
            chapter, section, subsection = key
            
            # Resolve heading name
            heading = subsection or section or chapter or "Unknown Section"
            
            # Identify warnings, steps, paragraphs in the group
            # We want to couple warnings with steps.
            # Let's iterate through the group elements.
            advisory_buffer = []
            processed_nodes = []
            
            for el in group_els:
                if el.content_type in (ContentType.WARNING, ContentType.CAUTION, ContentType.NOTE):
                    advisory_buffer.append(el)
                elif el.content_type == ContentType.HEADING:
                    # Headings can be skipped for text content, or added. Let's not chunk headings as standalone.
                    continue
                else:
                    # Paragraph, Step, Narrative Table
                    node_text = el.text
                    has_warning = False
                    has_caution = False
                    
                    # Merge any warnings/cautions/notes in the buffer with this element
                    if advisory_buffer:
                        adv_texts = []
                        for adv in advisory_buffer:
                            adv_texts.append(f"[{adv.content_type.value.upper()}] {adv.text}")
                            if adv.content_type == ContentType.WARNING:
                                has_warning = True
                            elif adv.content_type == ContentType.CAUTION:
                                has_caution = True
                        
                        node_text = "\n".join(adv_texts) + "\n" + node_text
                        advisory_buffer = []
                        
                    processed_nodes.append({
                        "element": el,
                        "text": node_text,
                        "has_warning": has_warning,
                        "has_caution": has_caution
                    })
            
            # If any warnings are left in buffer, append them to the last node
            if advisory_buffer and processed_nodes:
                adv_texts = []
                for adv in advisory_buffer:
                    adv_texts.append(f"[{adv.content_type.value.upper()}] {adv.text}")
                processed_nodes[-1]["text"] += "\n" + "\n".join(adv_texts)
                
            # Now, partition the processed nodes of this subsection.
            # Narrative tables should be separate chunks.
            # Sequential steps should be kept together in a single chunk.
            # Paragraphs can be grouped.
            # Let's build runs of chunks.
            current_chunk_nodes = []
            
            for node in processed_nodes:
                el = node["element"]
                # If it's a narrative table, emit the current chunk, and make the table its own chunk
                if el.content_type == ContentType.TABLE_NARRATIVE:
                    if current_chunk_nodes:
                        chunks.append(Chunker._create_chunk(current_chunk_nodes, key, heading, version_id, len(chunks)))
                        current_chunk_nodes = []
                    chunks.append(Chunker._create_chunk([node], key, heading, version_id, len(chunks)))
                else:
                    current_chunk_nodes.append(node)
            
            if current_chunk_nodes:
                chunks.append(Chunker._create_chunk(current_chunk_nodes, key, heading, version_id, len(chunks)))

        return chunks

    @staticmethod
    def _create_chunk(nodes: List[dict], key: tuple, heading: str, version_id: str, chunk_global_idx: int) -> Chunk:
        chapter, section, subsection = key
        
        # Build text with injected context prefix
        prefix_parts = []
        if chapter:
            prefix_parts.append(f"Chapter: {chapter}")
        if section:
            prefix_parts.append(f"Section: {section}")
        if subsection:
            prefix_parts.append(f"Subsection: {subsection}")
            
        prefix = " | ".join(prefix_parts) + "\n\n"
        
        body_text = "\n\n".join([n["text"] for n in nodes])
        text = prefix + body_text
        
        # Generate stable chunk ID
        sec_str = section.replace(" ", "_") if section else "none"
        sub_str = subsection.replace(" ", "_") if subsection else "none"
        chunk_id = f"ch_{chunk_global_idx:04d}_{sec_str}_{sub_str}"
        
        # Collect metadata attributes
        has_warning = any(n["has_warning"] for n in nodes)
        has_caution = any(n["has_caution"] for n in nodes)
        
        # Extract step numbers
        step_numbers = []
        for n in nodes:
            el = n["element"]
            if el.content_type == ContentType.STEP:
                # Find step number from text, e.g. "1. Do something" -> "1"
                match = re.match(r'^(\d+)\.', el.text)
                if match:
                    step_numbers.append(match.group(1))

        # Check content type of chunk
        first_el = nodes[0]["element"]
        content_type = first_el.content_type
        if any(n["element"].content_type == ContentType.STEP for n in nodes):
            content_type = ContentType.STEP
            
        # Extract effectivity
        effectivity = None
        effectivity_pattern = re.compile(r'(?:effectivity|effective for|s/n|serial numbers?:?)\s*([^\n.]+)', re.IGNORECASE)
        for n in nodes:
            match = effectivity_pattern.search(n["text"])
            if match:
                effectivity = match.group(1).strip()
                break

        # Extract related procedures (ATA cross references in format XX-XX-XX)
        related = []
        ata_ref_pattern = re.compile(r'\b\d{2}-\d{2}-\d{2}\b')
        for n in nodes:
            matches = ata_ref_pattern.findall(n["text"])
            related.extend(matches)
        related = list(set(related))
        
        # Extract ATA code from chapter or text
        # If chapter contains ATA XX, extract it
        ata_code = None
        if chapter:
            ata_match = re.search(r'ATA\s*(\d{2})', chapter, re.IGNORECASE)
            if ata_match:
                ata_code = f"ATA {ata_match.group(1)}"
        
        # Determine procedure phase
        procedure_phase = ProcedurePhase.UNKNOWN
        # Concatenate body text to classify
        full_body = body_text.lower()
        if any(word in full_body for word in ["setup", "preparation", "prepare", "tools", "materials", "equipment"]):
            procedure_phase = ProcedurePhase.PREPARATION
        elif any(word in full_body for word in ["remove", "install", "apply", "replace", "adjust", "torque"]):
            procedure_phase = ProcedurePhase.EXECUTION
        elif any(word in full_body for word in ["test", "inspect", "check", "verify", "acceptance", "functional check"]):
            procedure_phase = ProcedurePhase.VERIFICATION

        return Chunk(
            chunk_id=chunk_id,
            version_id=version_id,
            chapter=chapter,
            ata_code=ata_code,
            section=section,
            subsection=subsection,
            heading=heading,
            content_type=content_type,
            procedure_phase=procedure_phase,
            has_warning=has_warning,
            has_caution=has_caution,
            step_numbers=step_numbers,
            effectivity=effectivity,
            revision=None, # Will be set in metadata sync
            related_procedures=related,
            chunk_index=chunk_global_idx,
            text=text
        )
