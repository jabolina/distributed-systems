defmodule Sender do
  use GenServer
  use AMQP

  @queue  "distributed_systems"

  def start_link do
    GenServer.start_link(__MODULE__, [], [])
  end

  def init(_opts) do
    rabbitmq_connect()
  end

  defp rabbitmq_connect do
    case Connection.open do
      {:ok, connection} ->
        case Channel.open connection do
          {:ok, channel} ->
            IO.puts "Connected in RabbitMQ."

            AMQP.Queue.declare channel, @queue, durable: true

            send_message(channel)
          {:error, error} ->
            IO.puts "An error occurred while opening channel\n #{error}"
        end
      {:error, error} ->
        IO.puts "An error occurred while opening connection\n #{error}"
    end
  end

  defp send_message(channel) do
    case IO.gets ">: " do
      "exit" ->
        publish_message({:exit, channel})
      message ->
        publish_message({message, channel})
        send_message(channel)
    end
  end

  defp publish_message({:exit, _}) do
    IO.puts "Exit requested. Exiting..."
    Process.exit(:normal)
  end

  defp publish_message({message, channel}) do
    Basic.publish channel, "", @queue, message, persistent: true
    IO.puts "Sending message: #{message}"
  end

  def terminate(_, _) do
    IO.puts "Terminating client..."
  end
end
