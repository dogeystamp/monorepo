use std::{
    path::{Path, PathBuf},
    time::Duration,
};

use chrono::{DateTime, Local};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct Task {
    time_left: Duration,
    name: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct Period {
    start_time: chrono::DateTime<Local>,
    duration: Duration,
}

impl Period {
    fn get_end_time(&self) -> DateTime<Local> {
        self.start_time + self.duration
    }
}

#[derive(Serialize, Deserialize, Default, Debug)]
struct State {
    current_task: Option<Task>,
    current_session: Option<Period>,
}

fn read_state(state_file: &Path) -> Option<State> {
    let bytes = std::fs::read(state_file).ok()?;
    let content = str::from_utf8(&bytes).ok()?;
    serde_json::from_str(content).ok()
}

#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    command: Command,
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Subcommand)]
enum Command {
    /// Start break timer
    Start {
        /// Duration in minutes
        #[arg(default_value = "60")]
        duration: u64,
    },
    /// Get break/task status
    Status {},
}

fn main() {
    let state_dir =
        PathBuf::from(std::env::var("XDG_DATA_HOME").expect("XDG_DATA_HOME should be set"))
            .join("timer");
    let _ = std::fs::create_dir(&state_dir);
    let state_file = state_dir.join("timer.json");

    let mut state = read_state(&state_file).unwrap_or_default();

    let cli = Cli::parse();
    match cli.command {
        Command::Start { duration } => {
            state.current_session = Some(Period {
                start_time: chrono::offset::Local::now(),
                duration: Duration::from_mins(duration),
            })
        }
        Command::Status {} => {
            if let Some(ref session) = state.current_session {
                let delta = session.get_end_time() - chrono::offset::Local::now();
                let secs = delta.num_seconds();
                println!("session: {:>02}:{:>02} remaining", secs / 60, secs % 60,);
            }
        }
    }

    if cli.verbose {
        println!("{state:#?}");
    }

    std::fs::write(state_file, serde_json::to_string(&state).unwrap()).unwrap();
}
