use thiserror::Error;

#[derive(Debug, Error)]
pub enum Error {
    #[error("already started")]
    AlreadyStarted {},
}
