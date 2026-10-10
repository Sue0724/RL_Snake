"""Q 网络的维度兼容性、原始 Q 值及梯度更新检查。"""

import pytest
import torch

from algorithms.networks import DuelingQNetwork, QNetwork


@pytest.mark.parametrize("state_dim,n_actions", [(11, 3), (20, 3), (7, 4)])
def test_single_state_and_batch_use_requested_dimensions(state_dim, n_actions):
    net = QNetwork(state_dim, n_actions, hidden_dim=16)
    single = net(torch.zeros(state_dim))
    batch = net(torch.zeros(5, state_dim))
    assert single.shape == (n_actions,)
    assert batch.shape == (5, n_actions)
    assert torch.isfinite(batch).all()


def test_output_represents_values_including_negative_rewards():
    net = QNetwork(11, 3, hidden_dim=8)
    with torch.no_grad():
        for parameter in net.parameters():
            parameter.zero_()
        net.layers[-1].bias.copy_(torch.tensor([-10.0, 0.0, 10.0]))

    # 若误加了 softmax 或输出 ReLU，负 Q 值就无法保留。
    torch.testing.assert_close(net(torch.zeros(11)), torch.tensor([-10.0, 0.0, 10.0]))


def test_loss_can_backpropagate_and_optimizer_changes_parameters():
    torch.manual_seed(42)
    net = QNetwork(11, 3, hidden_dim=16)
    optimizer = torch.optim.Adam(net.parameters(), lr=1e-3)
    before = [parameter.detach().clone() for parameter in net.parameters()]
    actions = torch.tensor([0, 1, 2, 0])
    predictions = net(torch.randn(4, 11)).gather(1, actions[:, None]).squeeze(1)
    # 合成目标只用于梯度检查，不代表 DQN 的 Bellman 更新或训练结果。
    loss = torch.nn.functional.mse_loss(predictions, torch.tensor([10.0, -10.0, 0.0, 1.0]))
    optimizer.zero_grad()
    loss.backward()
    assert torch.isfinite(loss)
    assert all(parameter.grad is not None for parameter in net.parameters())
    assert all(torch.isfinite(parameter.grad).all() for parameter in net.parameters())
    optimizer.step()
    assert any(not torch.equal(old, new) for old, new in zip(before, net.parameters()))


@pytest.mark.parametrize("dimensions", [(0, 3, 16), (11, 0, 16), (11, 3, -1)])
def test_invalid_dimensions_are_rejected(dimensions):
    with pytest.raises(ValueError):
        QNetwork(*dimensions)


@pytest.mark.parametrize("shape", [(10,), (4, 20), (2, 3, 11)])
def test_incorrect_input_shape_is_rejected(shape):
    net = QNetwork(11, 3, hidden_dim=16)
    with pytest.raises(ValueError):
        net(torch.zeros(shape))


@pytest.mark.parametrize("state_dim,n_actions", [(11, 3), (20, 3), (7, 4)])
def test_dueling_network_single_state_and_batch_shapes(state_dim, n_actions):
    net = DuelingQNetwork(state_dim, n_actions, hidden_dim=16)
    assert net(torch.zeros(state_dim)).shape == (n_actions,)
    batch = net(torch.zeros(5, state_dim))
    assert batch.shape == (5, n_actions)
    assert torch.isfinite(batch).all()


def test_dueling_network_aggregates_value_and_mean_centered_advantage():
    net = DuelingQNetwork(11, 3, hidden_dim=8)
    with torch.no_grad():
        for parameter in net.parameters():
            parameter.zero_()
        net.value.bias.fill_(10.0)
        net.advantage.bias.copy_(torch.tensor([1.0, 2.0, 3.0]))

    # Q = V + A - mean(A)，因此 [9, 10, 11]。
    torch.testing.assert_close(net(torch.zeros(11)), torch.tensor([9.0, 10.0, 11.0]))

    # 给所有 action 的 Advantage 同加常数不应改变 Q，均值中心化必须生效。
    with torch.no_grad():
        net.advantage.bias.add_(100.0)
    torch.testing.assert_close(net(torch.zeros(11)), torch.tensor([9.0, 10.0, 11.0]))


@pytest.mark.parametrize("dimensions", [(0, 3, 16), (11, 0, 16), (11, 3, -1)])
def test_dueling_network_rejects_invalid_dimensions(dimensions):
    with pytest.raises(ValueError):
        DuelingQNetwork(*dimensions)
