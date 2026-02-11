"""Interactive setup wizard for Job Radar first-run configuration.

Collects user profile (name, skills, titles, location, dealbreakers) and
preferences (min_score, new_only) through sequential questionary prompts,
validates inputs inline, supports back navigation, and atomically writes
profile.json and config.json to platformdirs data directory.
"""

import json
import os
import tempfile
from pathlib import Path

import questionary
from questionary import Style, Validator, ValidationError


# Custom validators
class NonEmptyValidator(Validator):
    """Validate that input is not empty or whitespace-only."""

    def validate(self, document):
        if not document.text.strip():
            raise ValidationError(
                message="This field cannot be empty",
                cursor_position=len(document.text)
            )


class CommaSeparatedValidator(Validator):
    """Validate comma-separated list with minimum item count."""

    def __init__(self, min_items=1, field_name="item"):
        self.min_items = min_items
        self.field_name = field_name

    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(
                message=f"Please enter at least {self.min_items} {self.field_name}(s)"
            )

        items = [s.strip() for s in text.split(',') if s.strip()]
        if len(items) < self.min_items:
            raise ValidationError(
                message=f"Please enter at least {self.min_items} {self.field_name}(s)",
                cursor_position=len(document.text)
            )


class ScoreValidator(Validator):
    """Validate score is a float between 1.0 and 5.0."""

    def validate(self, document):
        text = document.text.strip()
        try:
            score = float(text)
            if not (1.0 <= score <= 5.0):
                raise ValidationError(
                    message="Score must be a number between 1.0 and 5.0",
                    cursor_position=len(document.text)
                )
        except ValueError:
            raise ValidationError(
                message="Score must be a number between 1.0 and 5.0",
                cursor_position=len(document.text)
            )


class YearsExperienceValidator(Validator):
    """Validate years of experience is a non-negative number."""

    def validate(self, document):
        text = document.text.strip()
        try:
            years = int(text)
            if years < 0:
                raise ValidationError(
                    message="Years must be 0 or greater",
                    cursor_position=len(document.text)
                )
            if years > 50:
                raise ValidationError(
                    message="Please enter a realistic number of years (0-50)",
                    cursor_position=len(document.text)
                )
        except ValueError:
            raise ValidationError(
                message="Please enter a whole number (e.g., 3, 5, 10)",
                cursor_position=len(document.text)
            )


class CompensationValidator(Validator):
    """Validate compensation is empty or a reasonable number."""

    def validate(self, document):
        text = document.text.strip()
        if not text:  # Empty is OK (optional field)
            return

        # Remove common formatting (commas, dollar signs, 'k')
        cleaned = text.replace(',', '').replace('$', '').strip()

        # Handle 'k' suffix (e.g., "120k" -> "120000")
        if cleaned.lower().endswith('k'):
            try:
                value = float(cleaned[:-1]) * 1000
            except ValueError:
                raise ValidationError(
                    message="Enter a number (e.g., 120000 or 120k)",
                    cursor_position=len(document.text)
                )
        else:
            try:
                value = float(cleaned)
            except ValueError:
                raise ValidationError(
                    message="Enter a number (e.g., 120000 or 120k)",
                    cursor_position=len(document.text)
                )

        if value < 0:
            raise ValidationError(
                message="Compensation must be positive",
                cursor_position=len(document.text)
            )
        if value > 1000000:
            raise ValidationError(
                message="Please enter a realistic compensation (under $1M)",
                cursor_position=len(document.text)
            )


# Custom style for cross-platform safe colors
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:green bold'),
    ('instruction', 'fg:ansigray'),
])


def _write_json_atomic(path: Path, data: dict):
    """Write JSON file atomically with temp file + rename to prevent corruption.

    Parameters
    ----------
    path : Path
        Target file path
    data : dict
        Data to write as JSON

    Notes
    -----
    Uses temp file in same directory + atomic rename to prevent partial writes
    on crash/interrupt. Ensures parent directory exists before writing.
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory (same filesystem for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp"
    )

    try:
        # Write JSON to temp file
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk

        # Atomic replace (works on Unix and Windows Python 3.3+)
        Path(tmp_path).replace(path)
    except:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except:
            pass
        raise


def is_first_run() -> bool:
    """Check if this is the first run by checking for profile.json existence.

    Returns
    -------
    bool
        True if profile.json does not exist, False otherwise
    """
    from .paths import get_data_dir
    return not (get_data_dir() / "profile.json").exists()


def run_setup_wizard() -> bool:
    """Run interactive setup wizard for first-run configuration.

    Prompts user for profile information (name, titles, skills, location,
    dealbreakers) and preferences (min_score, new_only), validates inputs,
    supports back navigation via /back command, displays celebration summary,
    and atomically writes profile.json and config.json.

    Returns
    -------
    bool
        True if wizard completed and files saved, False if user cancelled

    Notes
    -----
    Question order: Name -> Titles -> Skills -> Location -> Dealbreakers ->
    Score -> Filter (per CONTEXT.md decision WIZ-02).

    No default values on profile fields per CONTEXT.md decision WIZ-04.
    Score defaults to 2.8 per WIZ-08. new_only defaults to True.

    Mid-wizard back navigation: Type /back at any prompt to return to
    previous question.

    Post-summary editing: After summary, user can edit any field before saving.
    """
    from .paths import get_data_dir

    # Question definitions
    questions = [
        {
            'key': 'name',
            'type': 'text',
            'message': "What's your name?",
            'instruction': "e.g., John Doe",
            'validator': NonEmptyValidator(),
            'required': True,
        },
        {
            'key': 'years_experience',
            'type': 'text',
            'message': "Years of professional experience:",
            'instruction': "Enter a number (e.g., 3, 5, 10)",
            'validator': YearsExperienceValidator(),
            'required': True,
        },
        {
            'key': 'titles',
            'type': 'text',
            'message': "Target job titles:",
            'instruction': "e.g., Software Engineer, Full Stack Developer",
            'validator': CommaSeparatedValidator(min_items=1, field_name="job title"),
            'required': True,
        },
        {
            'key': 'skills',
            'type': 'text',
            'message': "Your core skills:",
            'instruction': "e.g., Python, JavaScript, React, AWS",
            'validator': CommaSeparatedValidator(min_items=1, field_name="skill"),
            'required': True,
        },
        {
            'key': 'location',
            'type': 'text',
            'message': "Location preference (optional):",
            'instruction': "e.g., Remote, New York, Boston area (press Enter to skip)",
            'validator': None,
            'required': False,
        },
        {
            'key': 'arrangement',
            'type': 'text',
            'message': "Work arrangement preference (optional):",
            'instruction': "e.g., Remote, Hybrid, On-site (press Enter to skip)",
            'validator': None,
            'required': False,
        },
        {
            'key': 'domain_expertise',
            'type': 'text',
            'message': "Industry/domain expertise (optional):",
            'instruction': "e.g., Healthcare, Fintech, E-commerce (press Enter to skip)",
            'validator': None,
            'required': False,
        },
        {
            'key': 'comp_floor',
            'type': 'text',
            'message': "Minimum compensation (optional):",
            'instruction': "e.g., 120000, 150k (press Enter to skip)",
            'validator': CompensationValidator(),
            'required': False,
        },
        {
            'key': 'dealbreakers',
            'type': 'text',
            'message': "Dealbreakers (optional):",
            'instruction': "e.g., relocation required, on-site only (press Enter to skip)",
            'validator': None,
            'required': False,
        },
        {
            'key': 'min_score',
            'type': 'text',
            'message': "Minimum job score (1.0-5.0)?",
            'instruction': "Enter a number from 1.0 to 5.0 (tip: 2.5-3.0 is a good starting point)",
            'validator': ScoreValidator(),
            'required': True,
            'default': "2.8",
        },
        {
            'key': 'new_only',
            'type': 'confirm',
            'message': "Show only new jobs (not previously seen)?",
            'instruction': None,
            'validator': None,
            'required': True,
            'default': True,
        },
    ]

    # Wizard header
    print("\n" + "=" * 60)
    print("🎯 Job Radar - First Time Setup")
    print("=" * 60)

    # Check if PDF parsing is available
    pdf_available = False
    try:
        from .pdf_parser import PDF_SUPPORT
        pdf_available = PDF_SUPPORT
    except ImportError:
        pass

    extracted_data = {}
    if pdf_available:
        print("\nSpeed up setup by uploading your resume PDF to auto-fill fields.\n")

        upload_choice = questionary.select(
            "How would you like to create your profile?",
            choices=[
                "Upload resume PDF",
                "Fill manually",
            ],
            style=custom_style
        ).ask()

        if upload_choice and "PDF" in upload_choice:
            # Prompt for file path
            pdf_path_str = questionary.path(
                "Path to your resume PDF:",
                only_directories=False,
                style=custom_style
            ).ask()

            if pdf_path_str:
                from pathlib import Path as _Path
                pdf_path = _Path(pdf_path_str)

                # Validate extension before calling parser
                if pdf_path.suffix.lower() != '.pdf':
                    print("\nFile must be a PDF (.pdf extension required)")
                elif not pdf_path.exists():
                    print(f"\nFile not found: {pdf_path}")
                else:
                    print(f"\nParsing resume PDF...\n")
                    try:
                        from .pdf_parser import extract_resume_data, PDFValidationError
                        extracted_data = extract_resume_data(pdf_path_str)

                        # Disclaimer - shown ONCE after parsing (CONTEXT.md locked decision)
                        print("Resume parsed successfully!")
                        print("\n  Please review - extraction may contain errors\n")

                        # Show what was extracted
                        if extracted_data:
                            print("Extracted fields:")
                            for key in extracted_data:
                                print(f"   - {key}")
                            print()

                    except PDFValidationError as e:
                        # Per CONTEXT.md: show specific actionable error message
                        print(f"\n{str(e)}\n")

                    except Exception as e:
                        # Catch-all for unexpected errors
                        print(f"\nPDF parsing encountered an error: {e}")
                        print("Continuing with manual entry...\n")
                        extracted_data = {}

                # If extraction failed or had errors, offer manual fallback
                # Per CONTEXT.md: "every error path ends with manual option"
                if not extracted_data and upload_choice and "PDF" in upload_choice:
                    fallback = questionary.confirm(
                        "Would you like to fill your profile manually?",
                        default=True,
                        style=custom_style
                    ).ask()

                    if not fallback:
                        return False

                    extracted_data = {}

    print("\nTip: Type /back at any prompt to return to the previous question.\n")

    # Sequential prompts with back navigation support
    answers = {}
    idx = 0

    while idx < len(questions):
        q = questions[idx]
        key = q['key']

        # Section headers
        if idx == 0:
            print("\n👤 Profile Information")
            print("-" * 40 + "\n")
        elif idx == 5:
            print("\n⚙️  Search Preferences")
            print("-" * 40 + "\n")

        # Build prompt kwargs
        prompt_kwargs = {
            'message': q['message'],
            'style': custom_style,
        }

        if q['instruction']:
            prompt_kwargs['instruction'] = q['instruction']

        if q.get('validator'):
            prompt_kwargs['validate'] = q['validator']

        # Pre-fill with previous answer if going back
        if key in answers:
            if q['type'] == 'text':
                prompt_kwargs['default'] = str(answers[key])
        elif key in extracted_data:
            # Pre-fill with PDF-extracted data (per CONTEXT.md: pre-display validation)
            value = extracted_data[key]
            if key == 'years_experience' and isinstance(value, int) and 0 <= value <= 50:
                prompt_kwargs['default'] = str(value)
            elif key == 'name' and isinstance(value, str) and value.strip() and len(value) < 100:
                prompt_kwargs['default'] = value
            elif key == 'titles' and isinstance(value, list) and value:
                prompt_kwargs['default'] = ', '.join(value)
            elif key == 'skills' and isinstance(value, list) and value:
                # Filter out overly long items (sanity check per CONTEXT.md)
                valid_skills = [s for s in value if len(s) < 50]
                if valid_skills:
                    prompt_kwargs['default'] = ', '.join(valid_skills)
        elif q.get('default') is not None and q['type'] == 'text':
            # Only use default for new answers on fields with defaults
            prompt_kwargs['default'] = q['default']

        # Ask question
        if q['type'] == 'text':
            result = questionary.text(**prompt_kwargs).ask()
        elif q['type'] == 'confirm':
            if key in answers:
                prompt_kwargs['default'] = answers[key]
            elif q.get('default') is not None:
                prompt_kwargs['default'] = q['default']
            result = questionary.confirm(**prompt_kwargs).ask()
        else:
            raise ValueError(f"Unknown question type: {q['type']}")

        # Handle Ctrl+C
        if result is None:
            if questionary.confirm(
                "Exit setup wizard?",
                default=False,
                style=custom_style
            ).ask():
                return False
            continue  # Re-prompt same question

        # Handle /back command
        if isinstance(result, str) and result.lower() == "/back":
            if idx > 0:
                idx -= 1
                print("\n← Going back...\n")
                continue
            else:
                print("\n⚠️  Already at first question.\n")
                continue

        # Store answer and advance
        answers[key] = result
        idx += 1

    # Build profile data structure
    # Parse comma-separated lists
    target_titles = [s.strip() for s in answers['titles'].split(',') if s.strip()]
    core_skills = [s.strip() for s in answers['skills'].split(',') if s.strip()]

    # Derive level from years of experience
    years = int(answers['years_experience'])
    if years < 2:
        level = "junior"
    elif years < 5:
        level = "mid"
    elif years < 10:
        level = "senior"
    else:
        level = "principal"

    profile_data = {
        "name": answers['name'],
        "years_experience": years,
        "level": level,
        "target_titles": target_titles,
        "core_skills": core_skills,
    }

    # Optional fields - only include if non-empty
    if answers.get('location') and answers['location'].strip():
        profile_data['location'] = answers['location'].strip()

    if answers.get('arrangement') and answers['arrangement'].strip():
        arrangement_list = [s.strip().lower() for s in answers['arrangement'].split(',') if s.strip()]
        if arrangement_list:
            profile_data['arrangement'] = arrangement_list

    if answers.get('domain_expertise') and answers['domain_expertise'].strip():
        domain_list = [s.strip() for s in answers['domain_expertise'].split(',') if s.strip()]
        if domain_list:
            profile_data['domain_expertise'] = domain_list

    if answers.get('comp_floor') and answers['comp_floor'].strip():
        comp_text = answers['comp_floor'].strip()
        # Parse compensation (handle $, commas, k suffix)
        cleaned = comp_text.replace(',', '').replace('$', '').strip()
        if cleaned.lower().endswith('k'):
            comp_value = int(float(cleaned[:-1]) * 1000)
        else:
            comp_value = int(float(cleaned))
        profile_data['comp_floor'] = comp_value

    if answers.get('dealbreakers') and answers['dealbreakers'].strip():
        dealbreakers_list = [s.strip() for s in answers['dealbreakers'].split(',') if s.strip()]
        if dealbreakers_list:
            profile_data['dealbreakers'] = dealbreakers_list

    # Get data directory for path resolution
    data_dir = get_data_dir()

    # Build config data structure
    config_data = {
        "min_score": float(answers['min_score']),
        "new_only": answers['new_only'],
        "profile_path": str(data_dir / "profile.json"),
    }

    # Celebration summary with post-summary editing loop
    while True:
        print("\n✨ All set! Here's your profile:")
        print("=" * 50)
        print("\n👤 Profile:")
        print(f"   Name: {profile_data['name']}")
        print(f"   Experience: {profile_data['years_experience']} years ({profile_data['level']} level)")
        print(f"   Titles: {', '.join(profile_data['target_titles'])}")
        print(f"   Skills: {', '.join(profile_data['core_skills'])}")
        print(f"   Location: {profile_data.get('location', '(not set)')}")

        arrangement_display = profile_data.get('arrangement')
        if arrangement_display:
            print(f"   Arrangement: {', '.join(arrangement_display)}")
        else:
            print(f"   Arrangement: (not set)")

        domain_display = profile_data.get('domain_expertise')
        if domain_display:
            print(f"   Industries: {', '.join(domain_display)}")

        comp_display = profile_data.get('comp_floor')
        if comp_display:
            print(f"   Min Compensation: ${comp_display:,}")

        dealbreakers_display = profile_data.get('dealbreakers')
        if dealbreakers_display:
            print(f"   Dealbreakers: {', '.join(dealbreakers_display)}")
        else:
            print(f"   Dealbreakers: (not set)")

        print("\n⚙️  Preferences:")
        print(f"   Minimum Score: {config_data['min_score']}")
        print(f"   New Jobs Only: {'Yes' if config_data['new_only'] else 'No'}")
        print("=" * 50 + "\n")

        # Ask to save or edit
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "Save this configuration",
                "Edit a field",
                "Cancel setup"
            ],
            style=custom_style
        ).ask()

        if action is None or action == "Cancel setup":
            print("\nSetup cancelled.")
            return False

        if action == "Save this configuration":
            break

        # Edit a field
        # Format compensation value
        comp_display = f"${profile_data['comp_floor']:,}" if profile_data.get('comp_floor') else '(not set)'

        field_choices = [
            f"Name ({profile_data['name']})",
            f"Experience ({profile_data['years_experience']} years - {profile_data['level']} level)",
            f"Titles ({', '.join(profile_data['target_titles'])})",
            f"Skills ({', '.join(profile_data['core_skills'])})",
            f"Location ({profile_data.get('location', '(not set)')})",
            f"Arrangement ({', '.join(profile_data.get('arrangement', [])) or '(not set)'})",
            f"Industries ({', '.join(profile_data.get('domain_expertise', [])) or '(not set)'})",
            f"Min Compensation ({comp_display})",
            f"Dealbreakers ({', '.join(profile_data.get('dealbreakers', [])) or '(not set)'})",
            f"Minimum Score ({config_data['min_score']})",
            f"New Jobs Only ({'Yes' if config_data['new_only'] else 'No'})",
        ]

        field_to_edit = questionary.select(
            "Which field would you like to edit?",
            choices=field_choices,
            style=custom_style
        ).ask()

        if field_to_edit is None:
            continue

        # Determine which field and re-prompt
        if field_to_edit.startswith("Name"):
            new_val = questionary.text(
                "What's your name?",
                default=profile_data['name'],
                validate=NonEmptyValidator(),
                style=custom_style
            ).ask()
            if new_val:
                profile_data['name'] = new_val

        elif field_to_edit.startswith("Experience"):
            new_val = questionary.text(
                "Years of professional experience:",
                default=str(profile_data['years_experience']),
                validate=YearsExperienceValidator(),
                style=custom_style
            ).ask()
            if new_val:
                years = int(new_val)
                profile_data['years_experience'] = years
                # Recalculate level
                if years < 2:
                    profile_data['level'] = "junior"
                elif years < 5:
                    profile_data['level'] = "mid"
                elif years < 10:
                    profile_data['level'] = "senior"
                else:
                    profile_data['level'] = "principal"

        elif field_to_edit.startswith("Titles"):
            new_val = questionary.text(
                "Target job titles:",
                default=', '.join(profile_data['target_titles']),
                validate=CommaSeparatedValidator(min_items=1, field_name="job title"),
                style=custom_style
            ).ask()
            if new_val:
                profile_data['target_titles'] = [s.strip() for s in new_val.split(',') if s.strip()]

        elif field_to_edit.startswith("Skills"):
            new_val = questionary.text(
                "Your core skills:",
                default=', '.join(profile_data['core_skills']),
                validate=CommaSeparatedValidator(min_items=1, field_name="skill"),
                style=custom_style
            ).ask()
            if new_val:
                profile_data['core_skills'] = [s.strip() for s in new_val.split(',') if s.strip()]

        elif field_to_edit.startswith("Location"):
            new_val = questionary.text(
                "Location preference (optional):",
                default=profile_data.get('location', ''),
                style=custom_style
            ).ask()
            if new_val is not None:
                if new_val.strip():
                    profile_data['location'] = new_val.strip()
                elif 'location' in profile_data:
                    del profile_data['location']

        elif field_to_edit.startswith("Arrangement"):
            current_arrangement = profile_data.get('arrangement', [])
            new_val = questionary.text(
                "Work arrangement preference (optional):",
                default=', '.join(current_arrangement) if current_arrangement else '',
                style=custom_style
            ).ask()
            if new_val is not None:
                if new_val.strip():
                    arrangement_list = [s.strip().lower() for s in new_val.split(',') if s.strip()]
                    if arrangement_list:
                        profile_data['arrangement'] = arrangement_list
                    elif 'arrangement' in profile_data:
                        del profile_data['arrangement']
                elif 'arrangement' in profile_data:
                    del profile_data['arrangement']

        elif field_to_edit.startswith("Industries"):
            current_industries = profile_data.get('domain_expertise', [])
            new_val = questionary.text(
                "Industry/domain expertise (optional):",
                default=', '.join(current_industries) if current_industries else '',
                style=custom_style
            ).ask()
            if new_val is not None:
                if new_val.strip():
                    domain_list = [s.strip() for s in new_val.split(',') if s.strip()]
                    if domain_list:
                        profile_data['domain_expertise'] = domain_list
                    elif 'domain_expertise' in profile_data:
                        del profile_data['domain_expertise']
                elif 'domain_expertise' in profile_data:
                    del profile_data['domain_expertise']

        elif field_to_edit.startswith("Min Compensation"):
            current_comp = profile_data.get('comp_floor')
            new_val = questionary.text(
                "Minimum compensation (optional):",
                default=str(current_comp) if current_comp else '',
                validate=CompensationValidator(),
                style=custom_style
            ).ask()
            if new_val is not None:
                if new_val.strip():
                    comp_text = new_val.strip()
                    cleaned = comp_text.replace(',', '').replace('$', '').strip()
                    if cleaned.lower().endswith('k'):
                        comp_value = int(float(cleaned[:-1]) * 1000)
                    else:
                        comp_value = int(float(cleaned))
                    profile_data['comp_floor'] = comp_value
                elif 'comp_floor' in profile_data:
                    del profile_data['comp_floor']

        elif field_to_edit.startswith("Dealbreakers"):
            current_dealbreakers = profile_data.get('dealbreakers', [])
            new_val = questionary.text(
                "Dealbreakers (optional):",
                default=', '.join(current_dealbreakers) if current_dealbreakers else '',
                style=custom_style
            ).ask()
            if new_val is not None:
                if new_val.strip():
                    dealbreakers_list = [s.strip() for s in new_val.split(',') if s.strip()]
                    if dealbreakers_list:
                        profile_data['dealbreakers'] = dealbreakers_list
                    elif 'dealbreakers' in profile_data:
                        del profile_data['dealbreakers']
                elif 'dealbreakers' in profile_data:
                    del profile_data['dealbreakers']

        elif field_to_edit.startswith("Minimum Score"):
            new_val = questionary.text(
                "Minimum job score (1.0-5.0)?",
                default=str(config_data['min_score']),
                validate=ScoreValidator(),
                style=custom_style
            ).ask()
            if new_val:
                config_data['min_score'] = float(new_val)

        elif field_to_edit.startswith("New Jobs Only"):
            new_val = questionary.confirm(
                "Show only new jobs (not previously seen)?",
                default=config_data['new_only'],
                style=custom_style
            ).ask()
            if new_val is not None:
                config_data['new_only'] = new_val

    # Write files atomically
    profile_path = data_dir / "profile.json"
    config_path = data_dir / "config.json"

    _write_json_atomic(profile_path, profile_data)
    _write_json_atomic(config_path, config_data)

    print(f"\n✅ Configuration saved to {data_dir}")
    print("You can now run job-radar to start searching!\n")

    return True
