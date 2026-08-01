use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::session::Session;

#[derive(Serialize, Deserialize, Default, Debug)]
pub struct State {
    pub current_session: Session,
}

pub fn read_state(state_file: &Path) -> Option<State> {
    let bytes = std::fs::read(state_file).ok()?;
    let content = str::from_utf8(&bytes).ok()?;
    serde_json::from_str(content).ok()
}
