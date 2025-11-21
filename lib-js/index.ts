
import { document_match, remove_trailing_dots, fix_tabs, all_dict_keys } from "./docassembleSrc.mjs";
import { readFileSync } from "fs";

//  TODO(brycew):
// * DA is fine with mixed case it looks like (i.e. Subquestion, vs subquestion)
// * what is "order"
// * can template and terms show up in same place?
// * can features and question show up in same place?
// * is "gathered" a valid attr?
// * handle "response"
// * labels above fields?
// * if "# use jinja" at top, process whole file with Jinja:
//   https://docassemble.org/docs/interviews.html#jinja2

// Ensure that if there's a space in the str, it's between quotes.
const space_in_str = /^[^ ]*['\"].* .*['\"][^ ]*$/

interface ErrorType {
    message: string;
    line_number: number;
}

interface BlockType {
    errors: Array<ErrorType>;
}

/**
 * Should be a direct YAML string, not a list or dict
 */
class YamlStr implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
        if (typeof x !== "string") {
            this.errors = [{
                "message": `${ x } isn't a string`,
                "line_number": 1
            }]
        }
    }
}

/**
 * A string that will be run through a Mako template from DA.
 * Needs to have a valid Mako template.
 */
class MakoText implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

/** 
 * A string that will be run through a Mako template from DA, then through a
 * markdown formatter. Needs to have valid Mako template.
 */
class MakoMarkdownText implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

/**
 * A full multiline python script. Should have valid python syntax. i.e. a code
 * block.
 */
class PythonText implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

/**
 * Some text that needs to explicitly be a python bool, i.e. True, False,
 * bool(1), but not 1
 */
class PythonBool implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

/**
 * Stuff that is considered Javascript, i.e. js show if
 */
class JavascriptText implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

/**
 * Things that need to be defined as a docassemble var, i.e. abc or x.y['a']
 */
class DAPythonVar implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

/**
 * Needs to be able to be a python defined types that's found at runtime in an interview, i.e. DAObject, Individual
 */
class DAType implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

class ObjectsAttrType implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

class DAFields implements BlockType {
    errors: Array<ErrorType>;

    constructor(x: any) {
        this.errors = []
    }
}

const big_dict = {
    "question": {
        "type": MakoMarkdownText
    }
}

const types_of_blocks = new Map<string, any>([
    [
        "include",
        {"exclusive": true, "allowed_attrs": ["include"]}
    ]
])

class YamlError {
    err_str: string;
    line_number: number;
    file_name: string;
    experimental: Boolean;

    constructor(err_str: string, line_number: number, file_name: string, experimental: Boolean) {
        this.err_str = err_str;
        this.line_number = line_number;
        this.file_name = file_name;
        this.experimental = experimental;
    }

    toString() {
        if (!this.experimental) {
            return `REAL ERROR: At ${this.file_name}:${this.line_number}: ${this.err_str}`;
        }
        return `At ${this.file_name}:${this.line_number}: ${this.err_str}`;
    }
}

function find_errors(input_file: string): Array<string> {
    var all_errors: Array<string> = [];

    const full_content = readFileSync(input_file).toString();

    const exclusive_keys = types_of_blocks.entries().filter(e => e[1].exclusive).map(e => e[0]);
    
    if (full_content.startsWith("# use jinja\n")) {
        console.log(`Ah Jinja! ignoring ${ input_file }`);
        return all_errors;
    }

    var lin_number = 1;
    for (var source_code of full_content.split(document_match)) {
        // lines_in_code = source_code.(l === "\n" sum(l == "\n" )
        source_code = source_code.replace(remove_trailing_dots, "")
        source_code = source_code.replace(fix_tabs, "  ")
        

    }

    return all_errors;
}

function process_file(input_file: string) {
    const dumb_da_files = ["pgcodecache.yml", "title_domentation.yml", "documentation.yml", "docstring.yml", "example-list.yml"]
    for (const dumb_da_file of dumb_da_files) {
        if (input_file.endsWith(dumb_da_file)) {
            console.log(`\nignoring ${dumb_da_file}`)
            return
        }
    }

    const all_errors = find_errors(input_file)

    if (all_errors.length == 0) {
        process.stdout.write(".")
        return
    }
    console.log(`\nFound ${ all_errors.length } errors:`)
    for (const err of all_errors) {
        console.log(`${err}`)
    }
}

// read the input file (1st arg)

// skip the file

function main() {
    for (const input_file of process.argv) {
        process_file(input_file)
    }
}