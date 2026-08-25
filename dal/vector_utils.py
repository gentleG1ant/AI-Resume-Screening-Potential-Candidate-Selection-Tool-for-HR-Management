import io
import scipy.sparse

def save_sparse_vector(matrix: scipy.sparse.csr_matrix) -> bytes:
    """
    Serializes a scipy.sparse matrix to bytes without using JSON.
    Uses an in-memory BytesIO buffer.
    """
    out_buffer = io.BytesIO()
    scipy.sparse.save_npz(out_buffer, matrix)
    return out_buffer.getvalue()

def load_sparse_vector(data_bytes: bytes) -> scipy.sparse.csr_matrix:
    """
    Deserializes a scipy.sparse matrix from bytes.
    """
    in_buffer = io.BytesIO(data_bytes)
    return scipy.sparse.load_npz(in_buffer)
