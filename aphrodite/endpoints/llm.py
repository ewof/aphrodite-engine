from typing import List, Optional, Union

from tqdm import tqdm
from transformers import PreTrainedTokenizer, PreTrainedTokenizerFast

from aphrodite.engine.args_tools import EngineArgs
from aphrodite.engine.aphrodite import AphroditeEngine
from aphrodite.common.outputs import RequestOutput
from aphrodite.common.sampling_params import SamplingParams
from aphrodite.common.utils import Counter


class LLM:
    """An LLM for generating texts from given prompts and sampling parameters.

    This class includes a tokenizer, a language model (possible distributed
    across multiple GPUs), and GPU memory space allocated for intermediate
    states (aka KV cache). Given a batch of prompts and sampling parameters,
    this class generates texts from the model, using an intelligent batching
    mechanism and efficient memory management.

    NOTE: This class is intended to be used for offline inference. For online
    serving, use the `AsyncAphrodite` class instead.
    NOTE: For the comprehensive list of arguments, see `EngineArgs`.

    Args:
        model: The name or path of a compatible HuggingFace Transformer model.
        tensor_parallel_size: The number of GPUs to use for distribtuted
            execution with tensor parallelism.
        dtype: The datatype for the model weights and activations. Currently 
            Aphrodite supports `float32`, `float16`, and `bfloat16`. If `auto`
            is used, it'll use the `torch_dtype` attribute specified in the model
            config file. However, if the `torch_dtype` in the config is `float32`,
            we will use `bfloat16` if your GPU supports it, otherwise `float16`.
        seed: The seed to initialize the RNG for sampling.
    """

    def __init__(
        self,
        model: str,
        tensor_parallel_size: int = 1,
        dtype: str = "auto",
        seed: int = 0,
        **kwargs,
    ) -> None:
        if "disable_log_stats" not in kwargs:
            kwargs["disable_log_stats"] = True
        engine_args = EngineArgs(
            model=model,
            tensor_parallel_size=tensor_parallel_size,
            dtype=dtype,
            seed=seed,
            **kwargs,
        )
        self.aphrodite = AphroditeEngine.from_engine_args(engine_args)
        self.request_counter = Counter()

    def get_tokenizer(
        self,
    ) -> Union[PreTrainedTokenizer, PreTrainedTokenizerFast]:
        return self.aphrodite.tokenizer
    
    def set_tokenizer(
        self,
        tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast],
    ) -> None: self.aphrodite.tokenizer = tokenizer

    def generate(
        self,
        prompts: Optional[Union[str, List[str]]] = None,
        sampling_params: Optional[SamplingParams] = None,
        prompt_token_ids: Optional[List[List[int]]] = None,
        use_tqdm: bool = True,
    ) -> List[RequestOutput]:
        """Generates the completions for the input prompts.

        NOTE: This class automatically batches the given prompts, considering the
        memory constraint. For the best performance, put all of your prompts into
        a single list and pass it to this method.

        Args:
            prompts: A list of prompts to generate completions for.
            sampling_params: The sampling parameters for text generation. If None,
                we use the default sampling parameters.
            prompt_token_ids: A list of token IDs for the prompts. If None, we
                use the tokenizer to convert the prompts to token IDs.
            use_tqdm: Whether to use tqdm to display the progress bar.

        Returns:
            A list of `RequestOutput` objects containing the generated completions
            in the same order as the input prompts.
        """
        if prompts is None and prompt_token_ids is None:
            raise ValueError("Either prompts or prompt_token_ids must be provided.")
        if isinstance(prompts, str):
            prompts = [prompts]
        if prompts is not None and prompt_token_ids is not None:
            if len(prompts) != len(prompt_token_ids):
                raise ValueError("The lenghts of prompts and prompt_token_ids must be the same.")
        if sampling_params is None:
            sampling_params = SamplingParams()

        if prompts is not None:
            num_requests = len(prompts)
        else:
            num_requests = len(prompt_token_ids)
        for i in range(num_requests):
            prompt = prompts[i] if prompts is not None else None
            if prompt_token_ids is None:
                token_ids = None
            else:
                token_ids = prompt_token_ids[i]
            self._add_request(prompt, sampling_params, token_ids)
        return self._run_engine(use_tqdm)

    def _add_request(
        self,
        prompt: Optional[str],
        sampling_params: SamplingParams,
        prompt_token_ids: Optional[List[int]],
    ) -> None:
        request_id = str(next(self.request_counter))
        self.aphrodite.add_request(request_id, prompt, sampling_params, prompt_token_ids)

    def _run_engine(self, use_tqdm: bool) -> List[RequestOutput]:
        if use_tqdm:
            num_requests = self.aphrodite.get_num_unfinished_requests()
            pbar = tqdm(total=num_requests, desc="Processed prompts")
        outputs: List[RequestOutput] = []
        while self.aphrodite.has_unfinished_requests():
            step_outputs = self.aphrodite.step()
            for output in step_outputs:
                if output.finished:
                    outputs.append(output)
                    if use_tqdm:
                        pbar.update(1)

        if use_tqdm:
            pbar.close()
        return outputs
    