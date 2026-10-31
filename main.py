#!/usr/bin/env python3

import argparse
import yaml
import json
import jsonschema
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Validates a service account configuration file against a JSON schema you supply. Privilege limits exist only if that schema encodes them.")
    parser.add_argument("config_file", help="Path to the configuration file (YAML or JSON).")
    parser.add_argument("schema_file", help="Path to the JSON schema file to validate the config against.")
    parser.add_argument("-l", "--log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help="Set the logging level.")
    parser.add_argument("-o", "--output_file", help="Path to the output file for the report (optional).")
    return parser.parse_args()

def load_config(config_file):
    """
    Loads configuration data from a YAML or JSON file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: Configuration data as a dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the file format is invalid or loading fails.
    """
    try:
        with open(config_file, 'r') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                try:
                    config_data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Error loading YAML file: {e}")
            elif config_file.endswith('.json'):
                try:
                    config_data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Error loading JSON file: {e}")
            else:
                raise ValueError("Unsupported file format.  Must be YAML or JSON.")
        return config_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    except Exception as e:
        raise ValueError(f"Error loading configuration file: {e}")


def load_schema(schema_file):
    """
    Loads a JSON schema from a file.

    Args:
        schema_file (str): Path to the schema file.

    Returns:
        dict: Schema data as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file is not valid JSON or loading fails.
    """
    try:
        with open(schema_file, 'r') as f:
            try:
                schema_data = json.load(f)
                return schema_data
            except json.JSONDecodeError as e:
                raise ValueError(f"Error loading JSON schema: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    except Exception as e:
        raise ValueError(f"Error loading schema file: {e}")

def validate_config(config_data, schema_data):
    """
    Validates the configuration data against the provided schema.

    Args:
        config_data (dict): Configuration data to validate.
        schema_data (dict): JSON schema to validate against.

    Returns:
        list: A list of validation errors (if any).  Empty list if validation passes.
        Each error is a dictionary containing 'message' and 'path'.

    Raises:
        jsonschema.exceptions.ValidationError: If the configuration does not match the schema.
    """
    try:
        # iter_errors collects every failure in one pass. validate stops
        # at the first, so a config missing three required keys heard
        # about one, fixed it, and had to run twice more to find the rest.
        validator_cls = jsonschema.validators.validator_for(schema_data)
        validator = validator_cls(schema_data)
        errors = []
        for e in validator.iter_errors(config_data):
            errors.append({
                "message": e.message,
                "path": ".".join(map(str, e.path)),
            })
        return errors
    except jsonschema.exceptions.SchemaError as e:
        raise ValueError(f"Invalid schema: {e}")
    except Exception as e:
        raise Exception(f"Unexpected validation error: {e}")



def generate_report(validation_errors):
    """
    Generates a report based on the validation errors.

    Args:
        validation_errors (list): A list of validation error dictionaries.

    Returns:
        str: A formatted report string.
    """
    if not validation_errors:
        return "Configuration validation successful. No issues found."

    report = "Configuration validation failed:\n"
    for error in validation_errors:
        report += f"  - Path: {error['path']}\n"
        report += f"    Message: {error['message']}\n"
    return report

def main():
    """
    Main function to orchestrate the configuration validation process.
    """
    try:
        args = setup_argparse()

        # Set log level based on argument
        logging.getLogger().setLevel(args.log_level.upper())

        logging.info("Starting chv-ServiceAccountPrivilegeChecker...")

        config_data = load_config(args.config_file)
        logging.info(f"Configuration file loaded: {args.config_file}")

        schema_data = load_schema(args.schema_file)
        logging.info(f"Schema file loaded: {args.schema_file}")

        validation_errors = validate_config(config_data, schema_data)
        logging.info("Configuration validation completed.")

        report = generate_report(validation_errors)

        if args.output_file:
            try:
                with open(args.output_file, 'w') as f:
                    f.write(report)
                logging.info(f"Report saved to: {args.output_file}")
            except Exception as e:
                # The report was the point of the run; losing it is a
                # failure even when the validation itself passed.
                logging.error(f"Error writing report to file: {e}")
                sys.exit(1)
        else:
            print(report)

        if validation_errors:
            sys.exit(1)  # Exit with an error code if validation failed

        logging.info("chv-ServiceAccountPrivilegeChecker completed successfully.")


    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)
    except ValueError as e:
        logging.error(e)
        sys.exit(1)
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Schema validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # This block used to write example config.yaml and schema.json files
    # into the working directory before calling main, on every run,
    # including --help. A checker that overwrites files named like the
    # caller's real inputs destroys the thing it was asked to check, so
    # the examples now live in this comment only:
    #
    # config.yaml:
    #   service_accounts:
    #     - name: web_server
    #       permissions: ["read", "write", "execute"]
    #
    # schema.json: a JSON schema requiring "service_accounts", with each
    # account requiring "name" and "permissions".
    #
    # Run: python main.py config.yaml schema.json
    main()